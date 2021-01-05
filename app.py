from flask import Flask, render_template, request
import os
import tweepy as tw
import pandas as pd
import re
import json
from pymongo import MongoClient
import pymongo
import logging
import multiprocessing
from datetime import datetime, timedelta

app = Flask(__name__)

# Link to Simon's database in mongodb atlas
MONGO_HOST = 'mongodb+srv://markusovich:Alexmom99@cluster0.enna3.mongodb.net/twitterdb?retryWrites=true&w=majority'
# Created a database named "twitterdb" in custer0

CONSUMER_KEY = "Duko8zJpuAMqAqOCGn3gLCdU7"
CONSUMER_SECRET = "K116dYN4lj0Ol4DGUsiCMAH8Vhz5tL02k3OPERWifGmwDLJ2rm"
ACCESS_TOKEN = "603210098-mkYuAJoQ5SptpC7laiENIFeyquRwCqPfA2XRTgt0"
ACCESS_TOKEN_SECRET = "vMeTce7nJffxEFDOGyNHrCHYIYIARP0IVywjaHPhg6oN8"

auth = tw.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tw.API(auth, wait_on_rate_limit=True,
             wait_on_rate_limit_notify=True)


def get_tweets(searchWord, location, date1, date2):

    searchWord += " -filter:retweets" + " -filter:replies"

    # Collect tweets
    tweets = tw.Cursor(api.search,
                       q=searchWord,
                       lang="en",
                       result_type="recent",
                       since=date1,
                       until=date2).items(1)

    client = MongoClient(MONGO_HOST)
    db = client.twitterdb

    # Iterate and print tweets
    for tweet in tweets:
        if location:
            if location in tweet._json['user']['location']:
                db.tweets.insert_one(tweet._json)
        else:
            db.tweets.insert_one(tweet._json)


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':

        MONGO_HOST = 'mongodb+srv://markusovich:Alexmom99@cluster0.enna3.mongodb.net/twitterdb?retryWrites=true&w=majority'

        disasterName = request.form['searchDisaster']
        locationName = request.form['searchLocation']
        dateRange = request.form['daterange']

        beginDate = datetime.today() - timedelta(days=int(dateRange))
        endDate = datetime.today()
        middleDate = beginDate + (endDate - beginDate)/2
        beginDate = beginDate.strftime('%Y-%m-%d')
        middleDate = middleDate.strftime('%Y-%m-%d')
        endDate = endDate.strftime('%Y-%m-%d')

        p1 = multiprocessing.Process(target=get_tweets, args=(
            disasterName, locationName, beginDate, middleDate))
        p2 = multiprocessing.Process(target=get_tweets, args=(
            disasterName, locationName, middleDate, endDate))

        p1.start()
        p2.start()

        p1.join()
        p2.join()

        return render_template('home.html')
    else:
        return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/tools")
def tools():
    return render_template('tools.html')


if __name__ == "__main__":
    app.run(debug=True)
