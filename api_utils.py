import requests
import datetime
import time
import response_status_code
import urllib

def connect_to_endpoint(url, headers):
    response = requests.request("GET", url, headers=headers)
    #429 is the rate-limit code
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

def connect_to_endpoint_stream(url, headers):
    response = requests.request("GET", url, headers=headers, stream=True)
    return response

def attach_params(url, params):
    for param_name, values in params.items():
        value_str = ','.join(values)
        url += f"&{param_name}={value_str}"
    return url

def create_convo_url(cid, params=None, next_token=None, max_results=100):
    if(max_results > 100): max_results = 100
    if(max_results < 10): max_results = 10
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

def create_timeline_id_url(uid, params=None, next_token = None, max_results=10):
    if(max_results > 100): max_results = 100
    if(max_results < 10): max_results = 10
    url = f"https://api.twitter.com/2/users/{uid}/tweets?&max_results={max_results}"
    if next_token:
        url += f"&pagination_token={next_token}"
    if params:
        url = attach_params(url, params)
    return url

def get_rules(headers):
    response = requests.get( "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers)
    if response.status_code != response_status_code.SUCCESS:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print('Got last rules')
    return response.json()

def delete_all_rules(headers, rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload
    )
    if response.status_code != response_status_code.SUCCESS:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print('Deleted Rules')

def set_rules(headers, query_rule_string):
    rules = [
        {"value": query_rule_string, "tag": query_rule_string},
    ]
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload,
    )
    if response.status_code != response_status_code.CREATION_SUCCESS:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(f'New rules set: {rules}')

def clear_and_set_rules(headers, query_rule_string):
    rules = get_rules(headers)
    delete_all_rules(headers, rules)
    set_rules(headers, query_rule_string)
    return

def filtered_stream_url(params):
    url = "https://api.twitter.com/2/tweets/search/stream?"
    if params:
        url = attach_params(url, params)
    return url

def sampled_stream_url(params):
    url = "https://api.twitter.com/2/tweets/sample/stream?"
    if params:
        url = attach_params(url, params)
    return url

#https://api.twitter.com/2/tweets/search/stream

def create_search_url(search_query, params=None, next_token=None, max_results=100):
    if max_results > 100: max_results = 100
    if max_results < 10: max_results = 10
    query = urllib.parse.quote(search_query)
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_results}"
    if next_token:
        url += f"&next_token={next_token}"
    if params:
        url = attach_params(url, params)
    return url

def create_all_search_url(search_query, start_time=None, end_time=None, params=None, next_token=None, max_results=100):
    if max_results > 500: max_results = 500
    if max_results < 10: max_results = 10
    query = urllib.parse.quote(search_query)
    url = f"https://api.twitter.com/2/tweets/search/all?query={query}&max_results={max_results}"
    if next_token:
        url += f"&next_token={next_token}"
    if params:
        url = attach_params(url, params)
    if start_time:
        url += f"&start_time={start_time}"
    if end_time:
        url += f"&end_time={end_time}"
    return url    

def create_username_profile_url(username, params=None):
    url = f"https://api.twitter.com/2/users/by/username/{username}?"
    url = attach_params(url, params)
    return url

def check_for_error(response_json):
    if 'errors' in response_json: 
        try:
            error_type = response_json['errors'][0]['type']
            error_message = response_json['errors'][0]['detail']
        except:
            try:
                error_type = response_json['errors'][0][0]['type']
                error_message = response_json['errors'][0][0]['detail']
            except:
                error_type = response_json['type']
                error_message = response_json['detail']
        
        print('ERROR TYPE, ', error_type)

        if error_type == response_status_code.INVALID_REQUEST:
            print('error!!')
            return response_status_code.INTERNAL_INVALID_REQUEST, error_message
        elif error_type == response_status_code.NOT_FOUND_ERROR:
            return response_status_code.INTERNAL_NOT_FOUND, error_message

    return response_status_code.INTERNAL_OK, ''
