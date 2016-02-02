# -*- coding: utf-8 -*-

#This program function
# save tweets into  a database
# if get deleted-stream then modify the saved tweet.

import json
import pytz
import sqlite3
import dateutil.parser
from datetime import datetime
import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

consumer_key        = "****"
consumer_secret     = "****"
access_token        = "****"
access_token_secret = "****"
zone = pytz.timezone('Asia/Tokyo')

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

connector = sqlite3.connect("./tweets.db")
cur = connector.cursor()
cur.execute("create table if not exists tweet(tweet_id int, user_id text, user_name text, user_screen_name text, tweet_text text, time text, deleted int, deleted_at text);")
connector.commit()
connector.close()


class StdOutListener(StreamListener):
    def on_data(self, data):
        status = json.loads(data)

        connector = sqlite3.connect("./tweets.db")
        cur = connector.cursor()
        
        if "text" in status:
            #change time-zone
            d = dateutil.parser.parse(status["created_at"])\
                               .astimezone(pytz.timezone('Asia/Tokyo'))\
                               .replace(tzinfo=pytz.timezone('Asia/Tokyo'))
            insert_data = (status["id"],\
                           status["user"]["id"],\
                           status["user"]["name"],\
                           status["user"]["screen_name"],\
                           status["text"],\
                           d,\
                           0,\
                           "none"\
                       )
            cur.execute("insert into tweet values(?,?,?,?,?,?,?,?)", insert_data)
            connector.commit()
            

        if "delete" in status:
            tweet_id = status["delete"]["status"]["id"]
            try:
                check_delete = 0
                cur.execute("select user_name, user_screen_name, tweet_text, time, deleted from tweet where tweet_id=?", (tweet_id,))
                for user_name, user_screen_name, tweet_text, time, deleted in cur:
                    message = u"%s %s\n----------\n%s\n----------\n%s"\
                              %(user_name, user_screen_name, tweet_text, time)
                    check_delete = int(deleted)
                if check_delete == 0:
                    d =  datetime.now()
                    cur.execute("update tweet set deleted=1, deleted_at=? where tweet_id=?", (d, tweet_id,))
                    connector.commit()
                        
            except:
                pass

        connector.close()
        
        return True


    def on_error(self, status):
        print status


if __name__ == '__main__':
    l = StdOutListener()
    d = datetime.now()

    stream = Stream(auth, l)
    stream.userstream()