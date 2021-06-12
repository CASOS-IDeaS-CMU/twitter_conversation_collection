import gzip
import json
import api_utils


def iterTweet(tweet):
    yield tweet
    if 'retweeted_status' in tweet:
        yield tweet['retweeted_status']
        if 'quoted_status' in tweet['retweeted_status']:
            yield tweet['retweeted_status']['quoted_status']
    if 'quoted_status' in tweet:
        yield tweet['quoted_status']


def quoteTweet(tweet):
    urls = tweet['entities']['urls']
    quotes = set()
    if len(urls) == 0:
        pass
    else:
        for url in urls:
            urlstring = url['expanded_url']
            if '/status/' in urlstring:
                quote = urlstring.split('/status/')[-1]
                quote = quote.split('?s=')[0]
                try:
                    int(quote)  # if this doesn't pass it didn't meet the format
                    quotes.add(quote)
                except:
                    continue
    if 'quoted_status_permalink' in tweet:
        urlstring = tweet['quoted_status_permalink']['expanded']
        quote = urlstring.split('/status/')[-1]
        quote = quote.split('?s=')[0]
        quotes.add(quote)
    quotes = set(int(x) for x in quotes)
    return quotes


def findMissingTweets(files):
    if isinstance(files, str):
        files = [files]
    tweetsWithData = set()
    referencedTweets = set()
    for file in files:
        if file.endswith('.gz'):
            opener = gzip.open
        else:
            opener = open
        with opener(file) as f:
            print(f'checking {file} for missing tweets...')
            for i, line in enumerate(f):
                try:
                    supertweet = json.loads(line)
                except:
                    continue
                if len(supertweet) <= 1:
                    continue
                for tweet in iterTweet(supertweet):
                    tweetsWithData.add(tweet['id'])
                    if ('in_reply_to_status_id' in tweet) and (tweet['in_reply_to_status_id'] is not None):
                        referencedTweets.add(tweet['in_reply_to_status_id'])
                    if ('quoted_status_id' in tweet) and (tweet['quoted_status_id'] is not None):
                        referencedTweets.add(tweet['quoted_status_id'])
                    additional_quotes = quoteTweet(tweet)
                    referencedTweets.update(additional_quotes)
    missingTweets = referencedTweets.difference(tweetsWithData)
    return tweetsWithData, missingTweets


def crawl_replies():
    infiles = ['../../../COVID_openup/collected_May10_Jun22.json.gz',
               '../../../COVID_openup/tweets_through_May10.json.gz']
    tweet_outfile = 'reopen_fillin_tweets.json'
    user_outfile = 'reopen_fillin_users.json'

    parameters = {}
    parameters['expansions'] = ['author_id', 'entities.mentions.username',
                                'referenced_tweets.id', 'referenced_tweets.id.author_id']
    parameters['place.fields'] = ['contained_within', 'country', 'country_code', 'full_name',
                                  'geo', 'id', 'name', 'place_type']
    parameters['tweet.fields'] = ['author_id', 'context_annotations', 'conversation_id',
                                  'created_at', 'entities', 'geo', 'id', 'in_reply_to_user_id',
                                  'lang', 'referenced_tweets', 'text']
    parameters['user.fields'] = ['created_at', 'description', 'entities', 'id', 'location',
                                 'name', 'public_metrics', 'url', 'username', 'verified']

    tweetsWithData, missingTweets = findMissingTweets(infiles)
    headers = api_utils.get_headers()
    seen_users, seen_tweets = set(), set()
    r = 0
    with open(tweet_outfile, 'w') as f_tweets, open(user_outfile, 'w') as f_users:
        while len(missingTweets) > 0:
            print(f'starting round {r} with {len(missingTweets)} to collect')
            r += 1
            missingTweets = list(missingTweets)
            newlyReferenced = set()
            for i in range(0, len(missingTweets), 100):
                tids = missingTweets[i:i + 100]
                url = api_utils.create_tweet_url(tids, params=parameters)
                response = api_utils.connect_to_endpoint(url, headers)
                if response.status_code != 200:
                    raise Exception(response.status_code, response.text)
                response_json = response.json()
                tweet_list = response_json['data'] + response_json['includes'].get('tweets', [])
                if ('meta' in response_json) and ('next_token' in response_json['meta']):
                    print('need to paginate')
                for tweet in tweet_list:
                    if tweet['id'] not in seen_tweets:
                        line = json.dumps(tweet)
                        line += '\n'
                        f_tweets.write(line)
                        seen_tweets.add(tweet['id'])
                        if ('referenced_tweets' in tweet) and (tweet['referenced_tweets'] is not None):
                            for x in tweet['referenced_tweets']:
                                newlyReferenced.add(x['id'])
                for user in response_json['includes']['users']:
                    if user['id'] not in seen_users:
                        line = json.dumps(user)
                        line += '\n'
                        f_users.write(line)
                        seen_users.add(user['id'])
            tweetsWithData = tweetsWithData.union(set(missingTweets))
            missingTweets = newlyReferenced.difference(tweetsWithData)


if __name__ == '__main__':
    crawl_replies()
