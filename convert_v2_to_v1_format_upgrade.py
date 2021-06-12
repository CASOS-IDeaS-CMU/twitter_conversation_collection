import gzip
import json
import sys
import datetime as dt
from pathlib import Path

'''
python convert_v2_to_v1_format_upgrade.py json "../Temp Testing/test_convert(1).json.gz" "../Temp Testing/timeline_164422451_20210611_173026.json"
'''

def write_to_file_gzip(filename, data_list):
    print(filename)
    print("    Writing " + str(len(data_list)) + " tweets to file: " + filename)
    json_str = json.dumps(data_list[0], sort_keys=True) + "\n"      # JSON
    for tweet in data_list[1:]:
        json_str += json.dumps(tweet, sort_keys=True) + "\n" 
    json_bytes = json_str.encode('utf-8')            # UTF-8

    with gzip.open(filename, 'w') as fout:       # gzip
        fout.write(json_bytes)         


def write_to_file_json(filename, data_list):
    print("    Writing " + str(len(data_list)) + " tweets to file: " + filename)
    with open(filename, 'w') as outfile:
        for row in data_list:
            print(json.dumps(row, sort_keys=True), file=outfile)


def reformat_entities(v2_tweet):
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


def reformat_tweet(v2_tweet, referenced_tweets, authors_lookup):

    tweet = v2_tweet

    author = authors_lookup[tweet['author_id']]
    tweet['user'] = author

    tweet['id_str'] = tweet['id']
    tweet['coordinates'] = None

    dt_obj = dt.datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.000Z")
    tweet['created_at'] = dt_obj.strftime("%a %b %d %H:%M:%S +0000 %Y")

    tweet['entities'] = reformat_entities(tweet)

    if('referenced_tweets' in tweet):
        if(tweet['referenced_tweets'][0]['type'] not in ['retweeted', 'replied_to', 'quoted']):
            print("Didn't expect this type of referenced tweet: " + json.dumps(tweet, indent=4, sort_keys=True))
        for referenced_tweet in tweet['referenced_tweets']:
            if(referenced_tweet['type'] == 'retweeted'):
                reference_id = referenced_tweet['id']
                try:
                    tweet_lookup = referenced_tweets[reference_id]
                    tweet['retweeted_status'] = tweet_lookup
                    tweet['retweeted_status']['user'] = authors_lookup[tweet_lookup['author_id']]
                except:
                    print("Couldn't find retweeted tweet")

            if(referenced_tweet['type'] == 'replied_to'):
                tweet['in_reply_to_user_id_str'] = tweet['in_reply_to_user_id']
                tweet['in_reply_to_user_id'] = int(tweet['in_reply_to_user_id'])
                tweet['in_reply_to_status_id'] = int(referenced_tweet['id'])
                tweet['in_reply_to_status_id_str'] = referenced_tweet['id']

            if(referenced_tweet['type'] == 'quoted'):
                tweet['is_quote_status'] = True
                tweet['quoted_status_id'] = int(referenced_tweet['id'])
                tweet['quoted_status_id_str'] = referenced_tweet['id']
                reference_id = referenced_tweet['id']
                try:
                    tweet_lookup = referenced_tweets[reference_id]
                    tweet['quoted_status'] = tweet_lookup
                    tweet['quoted_status']['user'] = authors_lookup[tweet_lookup['author_id']]
                except:
                    print("Couldn't find quoted tweet")  

    return tweet


#Read in arguments
if(len(sys.argv) < 3):
    raise ValueError('Must enter output file format (json/gzip) and at least one file to convert.')
file_format = sys.argv[1]
if(file_format not in ['json', 'gz']):
    raise ValueError('Output file format must be json or gzip')
files_to_convert = sys.argv[2:]

file_counter = 0

#Convert each file
for input_file in files_to_convert:
    converted_list = []
    referenced_tweets = {}
    authors_lookup = {}

    #Read in the v2 data
    input_data = []
    print("File " + str(file_counter) + ":")
    print("    Reading in: " + input_file)
    if(input_file[-2:] == 'gz'):
        for line in gzip.open(input_file, 'r'): input_data.append(json.loads(line))
        full_dict = input_data[0]
    elif(input_file[-4:] == 'json'):
        with open(input_file, "r", encoding='utf-8') as f:
            full_dict = json.loads(f.read())
    else:
        raise ValueError('Cannot convert this file type - only json and gzip.')

    #Get referenced tweets info and convert date and entities to v1 format
    for referenced_tweet in full_dict['includes']['tweets']:
        dt_obj = dt.datetime.strptime(referenced_tweet['created_at'], "%Y-%m-%dT%H:%M:%S.000Z")
        referenced_tweet['created_at'] = dt_obj.strftime("%a %b %d %H:%M:%S +0000 %Y")
        referenced_tweet['entities'] = reformat_entities(referenced_tweet)
        referenced_tweets[referenced_tweet['id']] = referenced_tweet

    #Get author/user info and add screen_name field
    for author_info in full_dict['includes']['users']:
        author_info['screen_name'] = author_info['username']
        author_info['id_str'] = author_info['id']
        author_info['followers_count'] = author_info['public_metrics']['followers_count']
        author_info['friends_count'] = author_info['public_metrics']['following_count']
        author_info['favourites_count'] = 0
        author_info['statuses_count'] = author_info['public_metrics']['tweet_count']
        authors_lookup[author_info['id']] = author_info

    total_posts_in_file = 0

    #For each tweet, reformat date and entities and add in user info and referenced tweet info (if applicable)
    for tweet in full_dict['data']:
        v1_tweet = reformat_tweet(tweet, referenced_tweets, authors_lookup)
        converted_list.append(v1_tweet)       
        total_posts_in_file += 1   

    print("    Total posts in file: " + str(total_posts_in_file)) 

    base_filename = input_file
    if(base_filename[-3:] == '.gz'): base_filename = base_filename[:-3]
    if(base_filename[-5:] == '.json'): base_filename = base_filename[:-5]
    if(file_format == 'gzip'):
        write_to_file_gzip(base_filename + '_v1.json', converted_list)
    else:
        write_to_file_json(base_filename + '_v1.json', converted_list)

    file_counter += 1