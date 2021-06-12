# twitter_conversation_collection
Repository for collecting Twitter conversations using the V2 API

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

### Additional Utilities 
1. Convert from V2 to V1 format
As a standalone on console: 
```
python convert_v2_to_v1_format_upgrade.py <json/gzip output> "<INPUT GZIP>" "<OUTPUT GZIP/JSON>"
```

As part of a module
```
TW.convert_json_v2_to_v1('test_convert.json')
TW.convert_json_v2_to_v1('test_convert.json.gz')
```

TODO:
- streaming 
- historical collection
