import os
import time
import json
import file_utils
import api_utils
import response_status_code
import convert_v2_to_v1
import crawler_utils

class TwitterCollection():
    def __init__(self, BEARER_TOKEN=None):
        self.bearer_token = BEARER_TOKEN
        self.headers = {"Authorization": "Bearer {}".format(BEARER_TOKEN)}

    def get_bearer_token(self):
        return self.bearer_token

    def __get_headers(self):
        return self.headers

    def timeline_collection(self, user_ids, outdir='./outdir', max_results=10, num_tweets = 3200):
        '''
        Twitter API V2 Timeline Limit: Provides the last 3,200 tweets from a 
        timeline. 
        '''
        final_result_dir = file_utils.make_results_dir(outdir)
        if max_results > 100:
            max_results = 100
            print('max results has to be between 5 and 100')

        self.__get_timeline(user_ids, final_result_dir, max_results, num_tweets)

    def timeline_collection_from_file(self, filename, outdir='./outdir', max_results=20):
        if max_results > 100:
            max_results = 100
            print('max results has to be between 5 and 100')
        
        user_ids, errorlines = file_utils.read_lines_into_file(filename)
        final_result_dir = file_utils.make_results_dir(outdir)
        file_utils.write_array_to_file(errorlines, final_result_dir, label_string='file reading errors')

        self.__get_timeline(user_ids, final_result_dir, max_results)

    def full_convo_collection(self, convo_ids, outdir='./outdir', max_results=20):
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__get_full_convo(convo_ids, final_result_dir, max_results)

    def full_convo_collection_from_file(self, filename, outdir='./outdir', max_results=20):
        convo_ids, errorlines = file_utils.read_lines_into_file(filename)
        final_result_dir = file_utils.make_results_dir(outdir)
        file_utils.write_array_to_file(errorlines, final_result_dir, label_string='file reading errors')

        self.__get_full_convo(convo_ids, final_result_dir, max_results)
    
    def get_replies_from_tweet_gzip_file(self, infilename, outdir='./outdir'):
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__get_replies(infilename, final_result_dir)

    def recent_search_tweets(self, query, outdir='./outdir', max_results=10):
        '''
        query: string of different hashtags, e.g. '#BLM #Black Lives Matter'
        max_results: Number of desired tweets. 
        '''
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__recent_search_tweets(query, final_result_dir, max_results)

    def all_search_tweets(self, query, outdir='./outdir', start_time=None, end_time=None, max_results=100):
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__all_search_tweets(query, final_result_dir, start_time, end_time, max_results)

    def sampled_stream(self, outdir='./outdir'):
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__sampled_stream(final_result_dir)

    def filtered_stream(self, query, outdir='./outdir'):
        query_array = query.split(' ')
        query_array_joined = ' OR '.join(query_array)
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__filtered_stream(query_array_joined, final_result_dir)

    def profile_info_from_username_file(self, infilename, outdir='./outdir'):
        username_list, errorlines = file_utils.read_string_lines_into_file(infilename)
        final_result_dir = file_utils.make_results_dir(outdir)
        file_utils.write_array_to_file(errorlines, final_result_dir, label_string='file reading errors')
        self.__get_profiles_from_username(username_list, final_result_dir)

    '''
    =====================
    Timeline code 
    =====================
    '''

    def __get_replies(self, gzip_filename, final_result_dir):
        parameters = {}
        parameters['expansions'] = ['author_id', 'entities.mentions.username',
                                    'referenced_tweets.id', 'referenced_tweets.id.author_id']
        parameters['place.fields'] = ['contained_within', 'country', 'country_code', 'full_name', 'geo', 'id', 'name', 'place_type']
        parameters['tweet.fields'] = ['author_id', 'context_annotations', 'conversation_id',
                                    'created_at', 'entities', 'geo', 'id', 'in_reply_to_user_id',                                'lang', 'referenced_tweets', 'text']
        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id', 'location', 'name', 'public_metrics', 'url', 'username', 'verified']

        tweetsWithData, missingTweets = crawler_utils.findMissingTweets(gzip_filename)
        error_tweet_ids = []

        seen_users, seen_tweets = set(), set()
        round = 0
        while len(missingTweets) > 0:
            missingTweets = list(missingTweets)
            newlyReferenced = set()

            for i in range(0, len(missingTweets), 100):
                tweetids = missingTweets[i: i+100]
                url = api_utils.create_tweet_url(tweetids, params=parameters)
                response = api_utils.connect_to_endpoint(url, self.headers)

                if response.status_code == response_status_code.SUCCESS:
                    response_json = response.json()

                    if 'error' in response_json:
                        for error_tweet in response_json['error']:
                            error_tweet_id = error_tweet['value']
                            error_type = error_tweet['title']
                            error_tweet_ids.append(f'{error_tweet_id},{error_type}\n')

                    for new_tweet in response_json['data']:
                        tweet_id = new_tweet['id']
                        if tweet_id not in seen_tweets:
                            seen_tweets.add(tweet_id)
                        if ('referenced_tweets' in new_tweet) and (new_tweet['referenced_tweets'] is not None):
                            for x in new_tweet['referenced_tweets']:
                                newlyReferenced.add(x['id'])
                    
                    for new_user in response_json['includes']['users']:
                        user_id = new_user['id']
                        if user_id not in seen_users:
                            seen_users.add(user_id)

                    output_json = {}
                    output_json['data'] = response_json['data']
                    output_json['includes'] = response_json['includes']               

                    gzip_filename_out = gzip_filename.replace('.json.gz', '')
                    gzip_filename_out = gzip_filename_out.replace('.json.gzip', '')
                    gzip_filename_out = gzip_filename_out.replace('.json', '')
                    file_utils.write_response_json_to_gzip(response_json, os.path.join(final_result_dir, f'replies_{gzip_filename_out}_{round}.json.gz'))

            round += 1

            tweetsWithData = tweetsWithData.union(set(missingTweets))
            missingTweets = newlyReferenced.difference(tweetsWithData)

        file_utils.write_array_to_file(error_tweet_ids, final_result_dir, label_string='error tweets')


    def __get_full_convo(self, convo_ids, final_result_dir, max_results=5):
        parameters = {}
        parameters['expansions'] = ['author_id', 'entities.mentions.username',
                                    'referenced_tweets.id', 'referenced_tweets.id.author_id']
        parameters['place.fields'] = ['contained_within', 'country', 'country_code', 'full_name','geo', 'id', 'name', 'place_type']
        parameters['tweet.fields'] = ['author_id', 'context_annotations', 'conversation_id',
                                    'created_at', 'entities', 'geo', 'id', 'in_reply_to_user_id',
                                    'lang', 'referenced_tweets', 'text']
        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id', 'location','name', 'public_metrics', 'url', 'username', 'verified']

        error_convos = []
        for convo in convo_ids:
            if not isinstance(convo, int):
                error_convos.append(f'{convo}, {response_status_code.INTERNAL_INVALID_REQUEST}')
                continue

            total_tweets = 0
            round = 0
            keepCollecting = True
            next_token = None
            merged_response_json = {}

            while keepCollecting:
                url = api_utils.create_convo_url(convo, params=parameters, next_token=next_token, max_results=max_results-total_tweets)
                response = api_utils.connect_to_endpoint(url, self.headers)

                if response.status_code != response_status_code.SUCCESS:
                    print(response.status_code)

                else:
                    response_json = response.json()
                    error_exists = api_utils.check_for_error(response_json)
                    if error_exists[0] == response_status_code.INVALID_REQUEST:
                        error_convos.append(f'{convo}, {error_exists}')
                        keepCollecting = False 

                    else:
                        if(error_exists[0] == response_status_code.NOT_FOUND_ERROR):
                            error_convos.append(f'{convo}, {error_exists}')

                        if('data' in response_json):
                            merged_response_json = self.__merge_response_jsons(response_json, merged_response_json)
                            file_utils.write_response_json_to_gzip(response_json, os.path.join(final_result_dir, f'convo_{convo}_{round}_.json.gz'))

                            round += 1
                            total_tweets += len(response_json['data'])

                            if total_tweets >= max_results or 'next_token' not in response_json['meta']:
                                keepCollecting = False
                            else:
                                next_token = response_json['meta']['next_token']
                        else:
                            keepCollecting = False

            if(len(merged_response_json) > 0):
                file_utils.write_response_json_to_gzip(merged_response_json, os.path.join(final_result_dir, f'convo_{convo}_all_data_.json.gz'))

        
    def __get_timeline(self, user_ids, final_result_dir, max_results=100, num_tweets = 3200):

        parameters = {}
        parameters['expansions'] = ['author_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id']
        parameters['tweet.fields'] = ['attachments', 'author_id', 'conversation_id', 'created_at', 'entities', 'geo', 'id', 'in_reply_to_user_id', 'lang',
                        'possibly_sensitive', 'public_metrics', 'referenced_tweets', 'reply_settings',
                        'source', 'text', 'withheld']
        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id', 'location', 'name', 'public_metrics', 'url', 'username', 'verified', 'protected', 'withheld']

        error_users = []
        
        for user in user_ids:
            
            if not isinstance(user, int):
                error_users.append(f'{user}, {response_status_code.INTERNAL_INVALID_REQUEST}')
                continue
            
            total_tweets=0
            round=0
            keepCollecting = True
            next_token = None
            merged_response_json = {}
            
            while keepCollecting:    
                user = str(user).strip()
                url = api_utils.create_timeline_id_url(user, params=parameters, next_token = next_token, max_results=max_results)
                response = api_utils.connect_to_endpoint(url, self.headers)
        
                if response.status_code != response_status_code.SUCCESS:
                    print(response.json())
                    print(f'Twitter API Error: {response.status_code}')
                    keepCollecting = False
                    
                else:
                    response_json = response.json()
                    error_exists, error_message = api_utils.check_for_error(response_json)
                
                    if error_exists[0] == response_status_code.INVALID_REQUEST:
                        error_users.append(f'{user}, {error_exists}')
                        keepCollecting = False 

                    else:
                        
                        if(error_exists[0] == response_status_code.NOT_FOUND_ERROR):
                            error_users.append(f'{user}, {error_exists}')

                        if('data' in response_json):
                            merged_response_json = self.__merge_response_jsons(response_json, merged_response_json)
                            #file_utils.write_response_json_to_gzip(response_json, os.path.join(final_result_dir, f'timeline_{user}_{round}_.json.gz'))

                            round += 1
                            total_tweets += len(response_json['data'])

                            if total_tweets >= num_tweets or 'next_token' not in response_json['meta']:
                                keepCollecting = False
                            else:
                                next_token = response_json['meta']['next_token']
                        else:
                            keepCollecting = False

            if(len(merged_response_json) > 0):
                file_utils.write_response_json_to_gzip(merged_response_json, os.path.join(final_result_dir, f'timeline_{user}.json.gz'))
        

    '''
    ======================
    Search Tweets
    ======================
    '''

    def __recent_search_tweets(self, query, final_result_dir, max_results):
        search_type = 'recent_search'
        self.__do_search(search_type, query=query, final_result_dir=final_result_dir, start_time=None, end_time=None, max_results=max_results)

    def __all_search_tweets(self, query, final_result_dir, start_time=None, end_time=None, max_results=100):
        search_type = 'all_search'
        self.__do_search(search_type, query=query, final_result_dir=final_result_dir, start_time=start_time, end_time=end_time, max_results=max_results)


    def __do_search(self, search_type, query, final_result_dir, start_time, end_time, max_results):
        parameters = {}
        parameters['expansions'] = ['author_id', 'referenced_tweets.id', 'in_reply_to_user_id', 'geo.place_id', 'entities.mentions.username', 'referenced_tweets.id.author_id','attachments.media_keys']

        parameters['place.fields'] = ['contained_within', 'country', 'country_code', 'full_name','geo', 'id', 'name', 'place_type']

        parameters['tweet.fields'] = ['attachments','author_id','context_annotations', 'conversation_id','created_at','entities','geo', 'id','in_reply_to_user_id','lang', 'possibly_sensitive', 'public_metrics', 'referenced_tweets','reply_settings','source', 'text', 'withheld']

        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id',   'location', 'name', 'public_metrics', 'url', 'username', 'verified', 'profile_image_url']

        parameters['media.fields'] = ['duration_ms', 'height', 'media_key', 'preview_image_url', 'public_metrics', 'type', 'url', 'width']

        keepCollecting = True
        next_token = None
        round = 0
        total_tweets = 0
        merged_response_json = {}
        query_truncate = query[:10]

        while keepCollecting:
            if search_type == 'recent_search':
                url = api_utils.create_search_url(query, params=parameters, next_token=next_token, max_results=max_results)
            elif search_type == 'all_search':
                url = api_utils.create_all_search_url(query, start_time, end_time, params=parameters, next_token=next_token, max_results=max_results)

            response = api_utils.connect_to_endpoint(url, self.headers)
            if response.status_code != response_status_code.SUCCESS:
                print(response.json())
                print(f'Twitter API Error: {response.status_code}')
                keepCollecting = False
            else:
                response_json = response.json()
                error_exists, error_message = api_utils.check_for_error(response_json)
                
                if error_exists[0] == response_status_code.INVALID_REQUEST:
                    error_convos.append(f'{convo}, {error_exists}')
                    keepCollecting = False 

                else:
                    if(error_exists[0] == response_status_code.NOT_FOUND_ERROR):
                        error_convos.append(f'{convo}, {error_exists}')

                    if('data' in response_json):
                        merged_response_json = self.__merge_response_jsons(response_json, merged_response_json)
                        #This will write out each individual json response to file
                        #file_utils.write_response_json_to_gzip(response_json, os.path.join(final_result_dir, f'search_{query_truncate}_{round}_.json.gz'))

                        round += 1
                        total_tweets += len(response_json['data'])

                        if total_tweets >= max_results or 'next_token' not in response_json['meta']:
                            keepCollecting = False
                        else:
                            next_token = response_json['meta']['next_token']
                    else:
                        keepCollecting = False

        if(len(merged_response_json) > 0):
            file_utils.write_response_json_to_gzip(merged_response_json, os.path.join(final_result_dir, f'search_{query_truncate}_all_data_.json.gz'))

    '''
    ========================
    Profile Information
    =======================
    '''
    def __get_profiles_from_username(self, username_list, final_result_dir):
        parameters = {}
        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id', 'location', 'name', 'public_metrics', 'url', 'username', 'verified', 'protected', 'withheld']

        error_users = []
        for user in username_list:
            user = user.strip()
            url = api_utils.create_username_profile_url(user, params=parameters)
            response = api_utils.connect_to_endpoint(url, self.headers)

            if response.status_code == response_status_code.SUCCESS:
                response_json = response.json()

                error_exists, error_message = api_utils.check_for_error(response_json)
                if error_exists == response_status_code.INTERNAL_OK:
                    file_utils.write_response_json_to_json(response_json, os.path.join(final_result_dir, f'profile_{user}.json'))
                else:
                    error_users.append(f'{user}, {error_message}')

        file_utils.write_array_to_file(error_users, final_result_dir, label_string='error users')

    '''
    ========================
    Streaming Code 
    ========================
    '''

    def __sampled_stream(self, final_result_dir):
        print('Sampling stream...')

        parameters = {}
        parameters['expansions'] = ['author_id', 'referenced_tweets.id', 'in_reply_to_user_id', 'geo.place_id', 'entities.mentions.username', 'referenced_tweets.id.author_id','attachments.media_keys']

        parameters['place.fields'] = ['contained_within', 'country', 'country_code', 'full_name','geo', 'id', 'name', 'place_type']

        parameters['tweet.fields'] = ['attachments','author_id','context_annotations', 'conversation_id','created_at','entities','geo', 'id','in_reply_to_user_id','lang', 'possibly_sensitive', 'public_metrics', 'referenced_tweets','reply_settings','source', 'text', 'withheld']

        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id',   'location', 'name', 'public_metrics', 'url', 'username', 'verified', 'profile_image_url']

        parameters['media.fields'] = ['duration_ms', 'height', 'media_key', 'preview_image_url', 'public_metrics', 'type', 'url', 'width']

        total_tweets = 0
        round = 0
        keepCollecting = True

        while keepCollecting: 
            url = api_utils.sampled_stream_url(parameters)

            response = api_utils.connect_to_endpoint_stream(url, self.headers)

            if response.status_code == response_status_code.SUCCESS:

                total_json = []
                for response_line in response.iter_lines():
                    try:
                        response_line_json = json.loads(response_line)
                        total_json.append(response_line_json)
                    except:
                        pass

                outfilename = os.path.join(final_result_dir, f'stream_{round}.json.gz')
                file_utils.write_response_arr_to_gzip(total_json, outfilename)

                round += 1
                total_tweets += len(total_json)
                print(f'Collected {total_tweets} tweets')
                time.sleep(5)

            else:
                print(f'Twitter API Error: {response.status_code}, {response.text}')
                keepCollecting = False

    def __filtered_stream(self, query_array_joined, final_result_dir):
        api_utils.clear_and_set_rules(self.headers, query_array_joined)

        print('Getting filtered stream...')

        parameters = {}
        parameters['expansions'] = ['author_id', 'referenced_tweets.id', 'in_reply_to_user_id', 'geo.place_id', 'entities.mentions.username', 'referenced_tweets.id.author_id','attachments.media_keys']

        parameters['place.fields'] = ['contained_within', 'country', 'country_code', 'full_name','geo', 'id', 'name', 'place_type']

        parameters['tweet.fields'] = ['attachments','author_id','context_annotations', 'conversation_id','created_at','entities','geo', 'id','in_reply_to_user_id','lang', 'possibly_sensitive', 'public_metrics', 'referenced_tweets','reply_settings','source', 'text', 'withheld']

        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id',   'location', 'name', 'public_metrics', 'url', 'username', 'verified', 'profile_image_url']

        parameters['media.fields'] = ['duration_ms', 'height', 'media_key', 'preview_image_url', 'public_metrics', 'type', 'url', 'width']

        total_tweets = 0
        round = 0
        keepCollecting = True

        while keepCollecting: 
            url = api_utils.filtered_stream_url(parameters)

            response = api_utils.connect_to_endpoint_stream(url, self.headers)

            if response.status_code == response_status_code.SUCCESS:
                total_json = []
                for response_line in response.iter_lines():
                    try:
                        response_line_json = json.loads(response_line)
                        total_json.append(response_line_json)
                    except:
                        pass
                query_truncated = query_array_joined[10:]
                outfilename = os.path.join(final_result_dir, f'stream_{query_truncated}_{round}.json.gz')
                file_utils.write_response_arr_to_gzip(total_json, outfilename)

                round += 1
                total_tweets += len(total_json)
                print(f'Collected {total_tweets} tweets')
                time.sleep(5)

            else:
                print(f'Twitter API Error: {response.status_code}, {response.text}')
                keepCollecting = False


    '''
    ==================================
    V2 to V1 conversion
    ==================================
    '''

    def convert_gzip_v2_to_v1(self, gzip_filename):
        if not gzip_filename.endswith('.gz'):
            print('Wrong file type, should be gz')
            return

        full_dict, response_code = file_utils.read_gzip_json_file(gzip_filename)
        if response_code == response_status_code.INTERNAL_GZIP_FILE_ERROR:
            print('Gzip file error')
            return 

        output_filename = convert_v2_to_v1.convert_json(full_dict, gzip_filename)
        print(f'Conversion done, output file in {output_filename}')

    def convert_json_v2_to_v1(self, json_filename):
        if not json_filename.endswith('.json'):
            print('Wrong file type, should be json')
            return

        full_dict, response_code = file_utils.read_json_file(json_filename)
        if response_code == response_status_code.INTERNAL_JSON_FILE_ERROR:
            print('Json file error')
            return 

        output_filename = convert_v2_to_v1.convert_json(full_dict, json_filename)
        print(f'Conversion done, output file in {output_filename}')
        

    '''
    =====================
    Combine multiple response json code 
    =====================
    '''

    def __merge_response_jsons(self, response_json_to_add, merged_response_json=None):
        if(len(merged_response_json) == 0):
            merged_response_json = {'data':[], 'includes': {'users':[], 'tweets':[], 'places':[], 'media':[], 'polls':[]}, 'errors':[], 'meta':{}}
        for tweet in response_json_to_add['data']:
            merged_response_json['data'].append(tweet)
        self.__add__expansion_parameter_to_json('users', merged_response_json, response_json_to_add)
        self.__add__expansion_parameter_to_json('tweets', merged_response_json, response_json_to_add)
        self.__add__expansion_parameter_to_json('places', merged_response_json, response_json_to_add)
        self.__add__expansion_parameter_to_json('media', merged_response_json, response_json_to_add)
        self.__add__expansion_parameter_to_json('polls', merged_response_json, response_json_to_add)
        if('errors' in response_json_to_add):
            for error in response_json_to_add['errors']:
                merged_response_json['errors'].append(error)
        if(len(merged_response_json['meta']) == 0):
            merged_response_json['meta'] = response_json_to_add['meta']
        else:
            merged_response_json['meta']['oldest_id'] = response_json_to_add['meta']['oldest_id']
            merged_response_json['meta']['result_count'] += response_json_to_add['meta']['result_count']
        if('next_token' in response_json_to_add['meta']):
            merged_response_json['meta']['next_token'] = response_json_to_add['meta']['next_token']
        else:
            merged_response_json['meta'].pop('next_token', 'none')
        return merged_response_json
        

    def __add__expansion_parameter_to_json(self, parameter, merged_response_json, response_json_to_add):
        if(parameter in response_json_to_add['includes']):
            for expansion_obj in response_json_to_add['includes'][parameter]:
                merged_response_json['includes'][parameter].append(expansion_obj)
 
