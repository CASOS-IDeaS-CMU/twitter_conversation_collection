import json, gzip

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

def findMissingTweets(gzip_filename):
    tweetsWithData, referencedTweets = set(), set()

    with  gzip.open(gzip_filename, 'r') as f:
        for line in f:
            try:
                supertweet = json.loads(line)
            except:
                continue 

            if len(supertweet) <= 1: continue

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