import gzip
import json
import sys
import datetime as dt
from pathlib import Path

'''
python convert_v2_to_v1_standalone.py output_file_type input_file1 input_file2 ....
Arguments:
    - output_file_type: "json" or "gz"
    - input_files: any mix of json and gz files in v2 format, extension must be .json or .json.gz
Outputs:
    - An output file of the specified output_file_type will be created for each input file, with "v_1" appended
      to the input file name (before the .json or .json.gz), containing the input file's tweets in
      v1 format.
example: python convert_v2_to_v1_standalone.py json "test_file1.json.gz" "test_file2.json" "test_file3.json.gz"
'''

def write_to_file_gz(filename, data_list):
    print("    Writing " + str(len(data_list)) + " tweets to file: " + filename)
    json_str = ""
    for tweet in data_list:
        json_str += json.dumps(tweet, sort_keys=True) + "\n" 
    json_bytes = json_str.encode('utf-8')

    with gzip.open(filename, 'w') as fout:
        fout.write(json_bytes)         


def write_to_file_json(filename, data_list):
    print("    Writing " + str(len(data_list)) + " tweets to file: " + filename)
    with open(filename, 'w') as outfile:
        for tweet in data_list:
            print(json.dumps(tweet, sort_keys=True), file=outfile)


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

    dt_obj = dt.datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.000Z")
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
                        print("Couldn't find retweeted tweet")

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
                        print("Couldn't find quoted tweet")  

    return tweet


def process_tweet_dict (full_dict, converted_list, referenced_tweets, authors_lookup, index):

    username_to_id_lookup = {}

    #Get author/user info and add screen_name field
    for author_info in full_dict['includes']['users']:
        author_info['screen_name'] = author_info['username']
        author_info['id_str'] = author_info['id']
        try: author_info['followers_count'] = author_info['public_metrics']['followers_count']
        except: author_info['followers_count'] = 0
        try: author_info['friends_count'] = author_info['public_metrics']['following_count']
        except: author_info['friends_count'] = 0
        author_info['favourites_count'] = 0
        try: author_info['statuses_count'] = author_info['public_metrics']['tweet_count']
        except: author_info['statuses_count'] = 0
        authors_lookup[author_info['id']] = author_info
        username_to_id_lookup[author_info['username']] = author_info['id_str']

    #Get referenced tweets info and convert date and entities to v1 format
    if('includes' in full_dict and 'tweets' in full_dict['includes']):
        for referenced_tweet in full_dict['includes']['tweets']:
            referenced_tweets[referenced_tweet['id']] = reformat_tweet(referenced_tweet, {}, authors_lookup, username_to_id_lookup, True)

    total_posts_in_file = 0

    #For each tweet, reformat date and entities and add in user info and referenced tweet info (if applicable)
    for tweet in full_dict['data']:
        v1_tweet = reformat_tweet(tweet, referenced_tweets, authors_lookup, username_to_id_lookup)
        converted_list.append(v1_tweet)       
        total_posts_in_file += 1   

    print("    Total posts in file line " + str(index) + ": " + str(total_posts_in_file)) 

    return (converted_list, referenced_tweets, authors_lookup)


#Read in arguments
if(len(sys.argv) < 3):
    raise ValueError('Please enter output file format (json/gz) and at least one file to convert.')
file_format = sys.argv[1]
if(file_format not in ['json', 'gz']):
    raise ValueError('Output file format must be "json" or "gz"')
files_to_convert = sys.argv[2:]

#Convert each file
for file_num, input_file in enumerate(files_to_convert):
    converted_list = []
    referenced_tweets = {}
    authors_lookup = {}

    #Read in the v2 data
    input_data = []
    print("File " + str(file_num) + ":")
    print("    Reading in: " + input_file)

    if(input_file[-8:] == '.json.gz'):
        index = 0
        for line in gzip.open(input_file, 'r'): 
            full_dict = json.loads(line)
            (converted_list, referenced_tweets, authors_lookup) = process_tweet_dict(full_dict, converted_list, referenced_tweets, authors_lookup, index)
            index += 1

    elif(input_file[-5:] == '.json'):
        with open(input_file, "r", encoding='utf-8') as f:
            for index, line in enumerate(f):
                full_dict = json.loads(line)
                (converted_list, referenced_tweets, authors_lookup) = process_tweet_dict(full_dict, converted_list, referenced_tweets, authors_lookup, index)

    else:
        raise ValueError('Cannot convert this file type, file name must end in ".json" or  ".json.gz".')

    #Output the converted tweets to file of specified type 
    print("Writing out converted data")
    base_filename = input_file
    if(base_filename[-8:] == '.json.gz'): base_filename = base_filename[:-8]
    elif(base_filename[-5:] == '.json'): base_filename = base_filename[:-5]
    else:
        #already checked above, but just in case
        raise ValueError('Cannot convert this file type, file name must end in ".json" or  ".json.gz".')
    
    if(file_format == 'gz'):
        write_to_file_gz(base_filename + '_v1.json.gz', converted_list)
    else:
        write_to_file_json(base_filename + '_v1.json', converted_list)
