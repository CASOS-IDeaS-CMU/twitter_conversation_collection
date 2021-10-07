from datetime import datetime
import file_utils

def reformat_entities(v2_tweet, username_to_id_lookup):
    entities = {"annotations": [], "hashtags": [], "symbols": [], "user_mentions": [], "urls": []}
    if('entities' in v2_tweet):
        tweet_entities = v2_tweet['entities']
        num_done = 0
        if('annotations' in tweet_entities): 
            entities['annotations'] = tweet_entities['annotations']
            num_done += 1
        if('hashtags' in tweet_entities): 
            hashtag_list = []
            for hashtag in tweet_entities['hashtags']:
                hashtag_list.append({'text': hashtag['tag'], 'indices': [hashtag['start'], hashtag['end']]})
            entities['hashtags'] = hashtag_list
            num_done += 1
        if('symbols' in tweet_entities): 
            entities['symbols'] = tweet_entities['symbols']
            num_done += 1
        if('mentions' in tweet_entities):
            mention_list = []
            for mention in tweet_entities['mentions']:
                if('id' in mention):
                    mention_list.append({"id": int(mention['id']), "id_str": mention['id'], "screen_name": mention['username'], 'indices': [mention['start'], mention['end']]})
                elif(mention['username'] in username_to_id_lookup):
                    mention['id'] = username_to_id_lookup[mention['username']]
                    mention_list.append({"id": int(mention['id']), "id_str": mention['id'], "screen_name": mention['username'], 'indices': [mention['start'], mention['end']]})
                else:
                    mention_list.append({"screen_name": mention['username'], 'indices': [mention['start'], mention['end']]})
            entities['user_mentions'] = mention_list
            num_done += 1
        if('urls' in tweet_entities):
            url_list = []
            for url in tweet_entities['urls']:
                url_list.append({"url": url['url'], "expanded_url": url['expanded_url'], "display_url": url['display_url'], 'indices': [url['start'], url['end']]})
            entities['urls'] = url_list
            num_done += 1
    return entities


def reformat_tweet(v2_tweet, referenced_tweets, authors_lookup, username_to_id_lookup, is_reference_tweet=False):
    tweet = v2_tweet

    if(tweet['author_id'] in authors_lookup):
        author = authors_lookup[tweet['author_id']]
        tweet['user'] = author
    tweet['id_str'] = tweet['id']
    tweet['coordinates'] = None

    dt_obj = datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.000Z")
    tweet['created_at'] = dt_obj.strftime("%a %b %d %H:%M:%S +0000 %Y")

    tweet['entities'] = reformat_entities(tweet, username_to_id_lookup)

    if('in_reply_to_user_id' in tweet):
        tweet['in_reply_to_user_id_str'] = tweet['in_reply_to_user_id']
        tweet['in_reply_to_user_id'] = int(tweet['in_reply_to_user_id'])
        if(tweet['in_reply_to_user_id_str'] in authors_lookup):
            tweet['in_reply_to_screen_name'] = authors_lookup[tweet['in_reply_to_user_id_str']]['screen_name']


    if('referenced_tweets' in tweet):
        if(tweet['referenced_tweets'][0]['type'] not in ['retweeted', 'replied_to', 'quoted']):
            print("Didn't expect this type of referenced tweet: " + json.dumps(tweet, indent=4, sort_keys=True))
        for referenced_tweet in tweet['referenced_tweets']:
            if(referenced_tweet['type'] == 'retweeted'):
                reference_id = referenced_tweet['id']
                if(is_reference_tweet):
                    tweet['retweeted_status'] = {'id': int(referenced_tweet['id']), 'id_str': referenced_tweet['id']}
                else:
                    try:
                        tweet_lookup = referenced_tweets[reference_id]
                        tweet['retweeted_status'] = tweet_lookup
                        tweet['retweeted_status']['user'] = authors_lookup[tweet_lookup['author_id']]
                    except:
                        #print("Couldn't find retweeted tweet")
                        pass

            if(referenced_tweet['type'] == 'replied_to'):
                tweet['in_reply_to_status_id'] = int(referenced_tweet['id'])
                tweet['in_reply_to_status_id_str'] = referenced_tweet['id']
                if(tweet['in_reply_to_user_id_str'] in authors_lookup):
                    tweet['in_reply_to_screen_name'] = authors_lookup[tweet['in_reply_to_user_id_str']]['screen_name']

            if(referenced_tweet['type'] == 'quoted'):
                tweet['is_quote_status'] = True
                tweet['quoted_status_id'] = int(referenced_tweet['id'])
                tweet['quoted_status_id_str'] = referenced_tweet['id']
                if(is_reference_tweet):
                    tweet['quoted_status'] = {'id': int(referenced_tweet['id']), 'id_str': referenced_tweet['id']}
                else:
                    try:
                        reference_id = referenced_tweet['id']
                        tweet_lookup = referenced_tweets[reference_id]
                        tweet['quoted_status'] = tweet_lookup
                        tweet['quoted_status']['user'] = authors_lookup[tweet_lookup['author_id']]
                    except:
                        #print("Couldn't find quoted tweet")  
                        pass
    return tweet

def convert_json(json_full_dict, json_filename):
    converted_list = []
    referenced_tweets = {}
    authors_lookup = {}
    username_to_id_lookup = {}

    #Get author/user info and add screen_name field
    for author_info in json_full_dict['includes']['users']:
        author_info['screen_name'] = author_info['username']
        author_info['id_str'] = author_info['id']
        author_info['followers_count'] = author_info['public_metrics']['followers_count']
        author_info['friends_count'] = author_info['public_metrics']['following_count']
        author_info['favourites_count'] = 0
        author_info['statuses_count'] = author_info['public_metrics']['tweet_count']
        authors_lookup[author_info['id']] = author_info
        username_to_id_lookup[author_info['username']] = author_info['id_str']

    #Get referenced tweets info and convert date and entities to v1 format
    if('includes' in json_full_dict and 'tweets' in json_full_dict['includes']):
        for referenced_tweet in json_full_dict['includes']['tweets']:
            referenced_tweets[referenced_tweet['id']] = reformat_tweet(referenced_tweet, {}, authors_lookup, username_to_id_lookup, True)

    for tweet in json_full_dict['data']:
        v1_tweet = reformat_tweet(tweet, referenced_tweets, authors_lookup, username_to_id_lookup)
        converted_list.append(v1_tweet)
    
    json_out_filename = json_filename.replace('.json', '') + '_convertedtov1.json.gz'
    file_utils.write_response_json_to_gzip(converted_list, json_out_filename)

    return json_out_filename
