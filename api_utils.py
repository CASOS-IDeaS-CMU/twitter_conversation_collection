import requests
import datetime
import time
import response_status_code
import urllib

def connect_to_endpoint(url, headers):
    response = requests.request("GET", url, headers=headers)
    # 429 is the rate-limit code
    if response.status_code == response_status_code.RATE_LIMIT:
        reset_time = datetime.datetime.fromtimestamp(int(response.headers['x-rate-limit-reset']))
        now = datetime.datetime.now()
        delta = reset_time - now
        time2sleep = delta.total_seconds() + 2
        if time2sleep > 0:
            print(f'limit hit. sleeping for {time2sleep/60:.1f} minutes...')
            time.sleep(time2sleep)
            print('woke up!')
        response = connect_to_endpoint(url, headers)
    return response

def attach_params(url, params):
    for param_name, values in params.items():
        value_str = ','.join(values)
        url += f"&{param_name}={value_str}"
    return url

def create_convo_url(cid, params=None, next_token=None, max_results=100):
    url = f"https://api.twitter.com/2/tweets/search/recent?query=conversation_id:{cid}&max_results={max_results}"
    if next_token:
        url += f"&next_token={next_token}"
    if params:
        url = attach_params(url, params)
    return url

def create_tweet_url(tids, params=None):
    if not isinstance(tids, list):
        tids = [tids]
    tids = [str(x) for x in tids]
    tid_str = ','.join(tids)
    url = f"https://api.twitter.com/2/tweets?ids={tid_str}"
    if params:
        url = attach_params(url, params)
    return url

def create_timeline_id_url(uid, params=None, max_results=10):
    url = f"https://api.twitter.com/2/users/{uid}/tweets?&max_results={max_results}"
    if params:
        url = attach_params(url, params)
    return url

def create_stream_url(search_term, params):
    pass

#https://api.twitter.com/2/tweets/search/stream

def create_search_url(search_query, params=None, next_token=None, max_results=100):
    if max_results > 100:
        max_results = 100
        print('Max results by Twitter API can only be 100')
    query = urllib.parse.quote(search_query)
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_results}"
    if next_token:
        url += f"&next_token={next_token}"
    if params:
        url = attach_params(url, params)
    return url

def check_for_error(response_json):
    if 'errors' in response_json: 
        try:
            error_type = response_json['errors'][0]['type']
            error_message = response_json['errors'][0]['message']
        except:
            response_json['type']
            error_message = response_json['message']
        if error_type == response_status_code.INVALID_REQUEST:
            return response_status_code.INTERNAL_INVALID_REQUEST, error_message
        elif error_type == response_status_code.NOT_FOUND_ERROR:
            return response_status_code.INTERNAL_NOT_FOUND, error_message
    else:
        return response_status_code.INTERNAL_OK