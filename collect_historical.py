import requests
import json
import gzip
import time
import os
import datetime as dt

bearer_token = "AAAAAAAAAAAAAAAAAAAAAAVmNgEAAAAAUvYmQ85pJ4..." #Add your bearer token here
tweet_daily_limit = 1000000                         #Use to set max number of tweets to collect daily
start = dt.datetime(2021, 1, 18)                    #Specify date to start collecting data
end = dt.datetime(2021, 1, 20)                      #Specify date to stop collecting data
search_terms = 'fakeelection OR "fake election" OR electionfraud OR "election fraud"'   #Replace with desired search terms here
partial_file = ""                                   #If finishing a partial day, specify file to finish collecting from, otherwise set to ""
partial_file_num_tweets = 0                         #If finishing a partial day, specify the number of tweets already collected, otherwise set to 0


def get_academic_header():
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

def connect_to_endpoint(query, start_time, end_time, next_token=None, filename=None, results_dict=None):
    headers = get_academic_header()

    #Add additional parameters as needed
    params = {"query": query, "max_results":"500", "start_time": start_time, "end_time": end_time, "tweet.fields": "attachments,created_at,public_metrics,entities,geo,in_reply_to_user_id,lang,referenced_tweets,source", "expansions":"author_id,referenced_tweets.id,in_reply_to_user_id,attachments.media_keys,geo.place_id,entities.mentions.username,referenced_tweets.id.author_id", "media.fields":"public_metrics,url,duration_ms", "place.fields":"country,country_code,full_name,geo,id,name,place_type", "user.fields": "description,verified,location,created_at,public_metrics"}

    if(next_token is not None):
        url = "https://api.twitter.com/2/tweets/search/all?next_token={}".format(next_token)
    else:
        url = "https://api.twitter.com/2/tweets/search/all?"

    response = requests.request("GET", url, params=params, headers=headers)

    if response.status_code != 200:
        if(filename != None and results_dict != None):
            write_to_file(filename, results_dict)
        raise Exception(response.status_code, response.text)

    return response.json()

def add_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def write_to_file(filename, data_dict):
    print("Writing " + str(len(data_dict["data"])) + " tweets to file: " + filename)
    json_str = json.dumps(data_dict, sort_keys=True) + "\n"      #JSON
    json_bytes = json_str.encode('utf-8')            #UTF-8
    with gzip.open(filename, 'w') as fout:       #gzip
        fout.write(json_bytes)                       
    

add_folder("Results")
add_folder("PartialResults")

delta = end - start
days = []
for i in range(delta.days + 1):
    day = start + dt.timedelta(days=i)
    days.append(day.strftime("%Y-%m-%dT00:00:00Z"))

default = True

#Handle partial files (when there is an error in the collection process)
if(partial_file != "" and partial_file_num_tweets != 0):
    tweet_list = []
    for line in gzip.open(partial_file, 'r'): tweet_list.append(json.loads(line)) 
    results_dict = tweet_list[0]
    next_token = results_dict['meta']['next_token']
    default = False

if(default): day_count = len(days) - 1
else: day_count = 1
print("# of days: " + str(day_count))

#Collect tweets for each day specified (unless it's a partial file)
for day_index in range(day_count):
    start_time = days[day_index]
    end_time = days[day_index+1]
    temp_count = 0
    flag = True
    if(default):
        results_dict = {}
        count = 0 
        json_response = connect_to_endpoint(search_terms, start_time, end_time) 
    if(not default):
        count = partial_file_num_tweets
        json_response = connect_to_endpoint(search_terms, start_time, end_time, next_token)
    while flag:
        result_count = json_response['meta']['result_count']
        if result_count is not None and result_count > 0:
            for key in json_response:
                if(key == "data"):
                    if(key not in results_dict):
                        results_dict[key] = json_response[key]
                        if(not default): assert(False)  #should only be here if default=True
                    else:
                        results_dict[key] += json_response[key]
                elif(key == "includes"):
                    if(key not in results_dict):
                        if(not default): assert(False) #should only be here if default=True
                        results_dict[key] = json_response[key]
                    else:
                        for sub_key in json_response[key]:
                            if(sub_key not in results_dict[key]):
                                results_dict[key][sub_key] = json_response[key][sub_key]
                            else:
                                results_dict[key][sub_key] += json_response[key][sub_key]
                elif(key == "meta"):
                    results_dict[key] = json_response[key]

            count += result_count
            temp_count += result_count
            if temp_count >= 10000:
                write_to_file("PartialResults/" + start_time[0:10] + "_" +str(count)+ '.gzip', results_dict)
                temp_count = 0
            #print(json.dumps(json_response, indent=4, sort_keys=True))
        
        if count >= tweet_daily_limit:
            print("Hit tweet daily limit!")
            break

        if 'next_token' in json_response['meta']:
            next_token = json_response['meta']['next_token']
            time.sleep(5)
            filename = "PartialResults/" + start_time[0:10] + "_" +str(count)+ '.gzip'
            json_response = connect_to_endpoint(search_terms, start_time, end_time, next_token, filename, results_dict)
        else:
            flag = False

    write_to_file("Results/" + start_time[0:10] + '.json.gzip', results_dict)
    print("Total Tweet IDs saved: {}".format(count))