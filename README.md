# twitter_conversation_collection
Repository for collecting Twitter conversations using the V2 API

This is tested in Python 3.9

## Initializing
```
from TwitterCollection import TwitterCollection

TW = TwitterCollection("<YOUR TWITTER V2 BEARER TOKEN HERE>")
print(TW.get_bearer_token())
```
Unsure of how to get a bearer token? Check this out on how to get set up with the Twitter API and acquire a bearer token: https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api

## Using as a Python Module 
#### 1. Get Timeline for specified users. 
Max results default is 10. Collected data is stored in the user-specified outdir, in a folder named with the date and time of the function call.
```
user_ids = [164422451, 255516424]
TW.timeline_collection(user_ids, './outdir', max_results=10)
```
OR
Make a file with one user id per line:
```
user_id.txt

164422451
255516424
``` 

Then in python, run:
```
TW.timeline_collection_from_file('user_id.txt', './outdir', max_results=10)
```

#### 2. Get conversations. 
Max results default is 10 original tweets per conversation. Collected data is stored in the user-specified outdir, in a folder named with the date and time of the function call. Files ending in numbers are data from individual API calls. Files ending in 'all_data' are the combined data from all indvidual API calls for each conversation id. 
```
conversation_ids = [1446673407567925248, 1446490585456513032]
TW.full_convo_collection(conversation_ids, './outdir', max_results=10)
```
OR
Make a file with one conversation id per line:
```
convo_id.txt
1446673407567925248
1446490585456513032
``` 

Then in python, run:
```
TW.full_convo_collection_from_file('convo_id.txt', './outdir', max_results=10)
```
Note: If the conversations are no longer recent, you may get no data returned.

#### 3. Reply collection, or get missing tweets that are in a conversation or referenced in a conversation. 
The input file, infilename.json.gz, should be formatted with one tweet JSON object per line.  Collected data is stored in the user-specified outdir, in a folder named with the date and time of the function call.
```
TW.get_replies_from_tweet_gzip_file('infilename.json.gz', './outdir')
```

#### 4. Recent search, back 7 days.
Max results default is 100 tweets. Collected data is stored in the user-specified outdir, in a folder named with the date and time of the function call. Files ending in numbers are data from individual API calls. Files ending in 'all_data' are the combined data from all of the indvidual API calls.

```
TW.recent_search_tweets(query, outdir='./outdir', max_results=100)
For example: TW.recent_search_tweets('#blacklivesmatter #BLM', outdir='./search_outdir', max_results=100)
```

If you want to restrict by language, add `lang:en` where en is the language code:
```
TW.recent_search_tweets('#blacklivesmatter #BLM lang:en', outdir='./search_outdir')
```
For more information on building queries and query operators: https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query

#### 5. Full archive search.
Max results default is 100 tweets. Start time and end time can be included as UTC timestamps, otherwise it will just be the latest tweets. Collected data is stored in the user-specified outdir, in a folder named with the date and time of the function call. Files ending in numbers are data from individual API calls. Files ending in 'all_data' are the combined data from all of the indvidual API calls.

```
TW.all_search_tweets(query, outdir='./outdir', start_time=start_time, end_time=end_time, max_results=100)
```
For example:
```
start_time='2020-10-05T00:00:00Z'
end_time='2020-10-30T23:59:59Z'
TW.all_search_tweets('#blacklivesmatter #BLM', outdir='./outdir', start_time=start_time, end_time=end_time, max_results=100)
```
For more information on building queries and query operators: https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query

#### 6. Sampled stream.
You just get 1% of Twitter's conversation and it is not filtered. It goes on forever until you stop it by ctrl+C or killing the terminal.

```
TW.sampled_stream(outdir='./sampled_outdir')
```

Note that the response is different than the usual, it is one tweet per line. [TODO: write conversion scripts to make things uniform]
```
Sample response
{"data":{"id":"1410664522327621636","text":"RT @AAairty: น้องเล่อเหมือนจะแกะแผลตรงแขน จีซองคือลอคมือไว้แน่นมาก ฮืออออ  https://t.co/LrWUynXFWn"}}
{"data":{"id":"1410664522344398848","text":"RT @vindib_: the lack of oversight on public spending is much worse than the last time around thanks to the pandemic, but we need to be act…"}}
```

#### 7. Filtered Stream.
In which you get streaming data based on certain parameters, for now it is just hashtags.

To add a list of hashtags, separate them by space.

```
TW.filtered_stream('#Blacklivesmatters #BLM', outdir='./filtered_stream')
```

#### 8. Get profile information from a username file (note, not user-id).
Input text file, username.txt, should have a single username per line. Collected data is stored in the user-specified outdir, in a folder named with the date and time of the function call. Each username specified will have its own JSON file with the associated profile information.
```
TW.profile_info_from_username_file('username.txt', outdir='outdir')
```

## Additional Utilities 
#### 1. Convert from v2 to v1 format.
Converts tweet data from API v2 JSON format to API v1 JSON format for backwards compatibility with existing software. The input file should be in the format of the direct response JSON from Twitter API v2 (which is also the format returned from the recent_search_tweets, all_search_tweets, and full_convo_collection functions).

As a standalone on console: 
```
python convert_v2_to_v1_standalone.py <"json"/"gz" output type> "<INPUT1 JSON/JSON.GZ>" "<INPUT2 JSON/JSON.GZ>" ...
For example: python convert_v2_to_v1_standalone.py json "test_file1.json.gz" "test_file2.json" "test_file3.json.gz"
```

As part of a module
```
TW.convert_json_v2_to_v1('test_convert.json')
TW.convert_gzip_v2_to_v1('test_convert.json.gz')
```

TODO:
- streaming add more parameters
- get user following
