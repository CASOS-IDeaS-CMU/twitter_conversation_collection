import os

import file_utils
import api_utils
import response_status_code
import convert_v2_to_v1

class TwitterCollection():
    def __init__(self, BEARER_TOKEN=None):
        self.bearer_token = BEARER_TOKEN
        self.headers = {"Authorization": "Bearer {}".format(BEARER_TOKEN)}

    def get_bearer_token(self):
        return self.bearer_token

    def __get_headers(self):
        return self.headers

    def timeline_collection(self, user_ids, outdir, max_results=10):
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__get_timeline(user_ids, final_result_dir, max_results)

    def timeline_collection_from_file(self, filename, outdir, max_results=10):
        user_ids, errorlines = file_utils.read_lines_into_file(filename)
        final_result_dir = file_utils.make_results_dir(outdir)
        file_utils.write_array_to_file(errorlines, final_result_dir, label_string='file reading errors')

        self.__get_timeline(user_ids, final_result_dir, max_results)

    def full_convo_collection(self, convo_ids, outdir, max_results=10):
        final_result_dir = file_utils.make_results_dir(outdir)
        self.__get_full_convo(convo_ids, final_result_dir, max_results)

    def full_convo_collection_from_file(self, filename, outdir, max_results=10):
        convo_ids, errorlines = file_utils.read_lines_into_file(filename)
        final_result_dir = file_utils.make_results_dir(outdir)
        file_utils.write_array_to_file(errorlines, final_result_dir, label_string='file reading errors')

        self.__get_full_convo(convo_ids, final_result_dir, max_results)
    
    def get_replies_from_tweet_json_file(self, infilename):
        pass

    def __get_full_convo(self, convo_ids, final_result_dir, max_results=5):
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

        error_convos = []
        for convo in convo_ids:
            if not isinstance(convo, int):
                error_convos.append(f'{convo}, {response_status_code.INTERNAL_INVALID_REQUEST}')
                continue

            total_tweets = 0
            round = 0
            keepCollecting = True
            next_token = None
            while keepCollecting:
                url = api_utils.create_convo_url(convo, params=parameters, next_token=next_token)
                response = api_utils.connect_to_endpoint(url, self.headers)

                if response.status_code == response_status_code.SUCCESS:
                    response_json = response.json()

                error_exists = api_utils.check_for_error(response_json)
                if not error_exists == response_status_code.INTERNAL_OK:
                    error_convos.append(f'{convo}, {error_exists}')
                    keepCollecting = False 

                else:
                    file_utils.write_response_json_to_gzip(response_json, os.path.join(final_result_dir, f'convo_{convo}_{round}.json.gz'))

                    round += 1
                    total_tweets += len(response_json['data'])

                    if total_tweets >= max_results:
                        keepCollecting = False

    def __get_timeline(self, user_ids, final_result_dir, max_results=10):
        parameters = {}
        parameters['expansions'] = ['author_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id']
        parameters['tweet.fields'] = ['attachments', 'author_id', 'conversation_id', 'created_at',
                        'entities', 'geo', 'id', 'in_reply_to_user_id', 'lang',
                        'possibly_sensitive', 'public_metrics', 'referenced_tweets', 'reply_settings',
                        'source', 'text', 'withheld']
        parameters['user.fields'] = ['created_at', 'description', 'entities', 'id', 'location',
                                    'name', 'public_metrics', 'url', 'username', 'verified', 'protected', 'withheld']

        error_users = []

        for user in user_ids:
            if not isinstance(user, int):
                error_users.append(f'{user}, {response_status_code.INTERNAL_INVALID_REQUEST}')
                continue

            url = api_utils.create_timeline_id_url(user, params=parameters, max_results=max_results)
            response = api_utils.connect_to_endpoint(url, self.headers)

            if response.status_code == response_status_code.SUCCESS:
                response_json = response.json()

                error_exists = api_utils.check_for_error(response_json)
                if error_exists == response_status_code.INTERNAL_OK:
                    file_utils.write_response_json_to_gzip(response_json, os.path.join(final_result_dir, f'timeline_{user}.json.gz'))
                else:
                    error_users.append(f'{user}, {error_exists}')

        file_utils.write_array_to_file(error_users, final_result_dir, label_string='error users')

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
        
