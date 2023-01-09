# Import necessary libraries
import tweepy
from kafka import KafkaProducer
from json import loads, dumps
from time import sleep

# Set up the tweeter API
with open('twitter_api/twitterAPISulisB.json') as myapi:
    apiku=loads(myapi.read())
CONSUMER_KEY=apiku['consumer_key']
CONSUMER_SECRET=apiku['consumer_secret']
ACCESS_TOKEN=apiku['access_token']
ACCESS_TOKEN_SECRET=apiku['access_token_secret']
auth=tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Set up the Kafka producer
producer=KafkaProducer(bootstrap_servers=['localhost:9092'],
        value_serializer=lambda K:dumps(K).encode('utf-8'))
topic="investasi"

# scrape 1 tweet every 6 seconds, to prevent error: "TooManyRequests: 429 Too Many Requests"
# only send new tweet to kafka topic (ignore tweets that is the same as the tweet on previous scraping)
tweetmp=0
while(True):
    api=tweepy.API(auth)
    cursor=tweepy.Cursor(api.search_tweets,q="sukuk OR reksadana OR saham",
            tweet_mode='extended').items(1)
    for tweet in cursor:
        if tweet.id==tweetmp:
            sleep(6)
            continue
        # print(tweet._json)
        producer.send(topic, tweet._json)
        tweetmp=tweet.id
        sleep(6)
        # break