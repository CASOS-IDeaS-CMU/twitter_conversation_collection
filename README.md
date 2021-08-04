# twitter_conversation_collection
Repository for collecting Twitter conversations using the V2 API

This is tested in Python 3.9

### Initializing
```
from TwitterCollection import TwitterCollection

TW = TwitterCollection("<YOUR TWITTER V2 BEARER TOKEN HERE>")
print(TW.get_bearer_token())
```

### Using as a Python Module 
1. Get Timeline, max results default 10
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
TW.timeline_collection_from_file(user_id.txt, './outdir', max_results=10)
```

2. Get conversations, default max results of number of original tweets per convo is 10
```
conversation_ids = [1397267849920532481, 1397370626734661633]
TW.full_convo_collection(conversation_ids, './outdir', max_results=10)
```
OR
Make a file with one user id per line:
```
convo_id.txt
1397267849920532481
1397370626734661633
``` 

Then in python, run:
```
TW.full_convo_collection_from_file(user_id.txt, './outdir', max_results=10)
```

3. Reply collection, or get missing tweets that are in a convo or referenced in a convo
```
TW.get_replies_from_tweet_gzip_file('infilename.json.gz', './outdir')
```

4. Recent search, back 7 days, max 100 results
```
TW.recent_search_tweets('#blacklivesmatter #BLM', outdir='./search_outdir')
```

If you want to restrict by language, add `lang:en` where en is the language code
```
TW.recent_search_tweets('#blacklivesmatter #BLM lang:en', outdir='./search_outdir')
```

5. Full archive search
Start time and end time can be included as UTC timestamps, otherwise it will just be the latest tweets

```
TW.all_search_tweets('#blacklivesmatter #BLM', outdir='./outdir', start_time=start_time, end_time=end_time, max_results=100)

start_time='2020-10-05T00:00:00Z'
end_time='2020-10-30T23:59:59Z'

TW.all_search_tweets('#blacklivesmatter #BLM', outdir='./outdir', start_time=start_time, end_time=end_time, max_results=100)
```

6. Sampled stream
In which you just get 1% of Twitter's conversation and is not filtered. It goes on forever until you stop it by ctrl+C or killing the terminal.

```
TW.sampled_stream(outdir='./sampled_outdir')
```

Note that the response is different than the usual, it is one tweet per line. [TODO: write conversion scripts to make things uniform]
```
Sample response
{"data":{"id":"1410664522327621636","text":"RT @AAairty: น้องเล่อเหมือนจะแกะแผลตรงแขน จีซองคือลอคมือไว้แน่นมาก ฮืออออ  https://t.co/LrWUynXFWn"}}
{"data":{"id":"1410664522344398848","text":"RT @vindib_: the lack of oversight on public spending is much worse than the last time around thanks to the pandemic, but we need to be act…"}}
```

7. Filtered Stream
In which you get streaming data based on certain parameters, for now it is just hashtags.

To add a list of hashtags, separate them by space

```
TW.filtered_stream('#Blacklivesmatters #BLM', outdir='./filtered_stream')
```

8. Get profile information from a username file (note, not user-id)
Note it is a single username per line
```
TW.profile_info_from_username_file('username.txt', outdir='outdir')
```

### Additional Utilities 
1. Convert from V2 to V1 format
As a standalone on console: 
```
python convert_v2_to_v1_standalone.py <"json"/"gz" output type> "<INPUT1 JSON/JSON.GZ>" "<INPUT2 JSON/JSON.GZ>" ...
For example: python convert_v2_to_v1_standalone.py json "test_file1.json.gz" "test_file2.json" "test_file3.json.gz"
```

As part of a module
```
TW.convert_json_v2_to_v1('test_convert.json')
TW.convert_json_v2_to_v1('test_convert.json.gz')
```

TODO:
- streaming add more parameters
- get user following