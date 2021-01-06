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
import pickle

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

parser = pickle.load(open('parser.sav', 'rb'))


def model_prediction(text):
    true = 0
    false = 0
    for item in os.listdir("models/"):
        model = pickle.load(open("models/{}".format(item), 'rb'))
        prediction = model.predict(parser.transform([text]))[0]
        if prediction == "T":
            true += 1
        else:
            false += 1

    return true > false


def get_tweets(searchWord, location, date1, date2):

    searchWord += " -filter:retweets" + " -filter:replies"

    # Collect tweets
    tweets = tw.Cursor(api.search,
                       q=searchWord,
                       lang="en",
                       since=date1,
                       until=date2).items(1)

    client = MongoClient(MONGO_HOST)
    db = client.twitterdb

    # Iterate and print tweets
    for tweet in tweets:
        if location:
            if location in tweet._json['user']['location']:
                if model_prediction(tweet._json['text']):
                    db.tweets.insert_one(tweet._json)
        else:
            if model_prediction(tweet._json['text']):
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
        firstquarterDate = beginDate + (endDate - beginDate)/4
        firstthirdDate = beginDate + (endDate - beginDate)/3
        middleDate = beginDate + (endDate - beginDate)/2
        secondthirdDate = beginDate + (endDate - beginDate)/3 *2
        thirdquarterDate = beginDate + (endDate - beginDate)/4 * 3

        beginDate = beginDate.strftime('%Y-%m-%d')
        firstquarterDate = firstquarterDate.strftime('%Y-%m-%d')
        firstthirdDate = firstthirdDate.strftime('%Y-%m-%d')
        middleDate = middleDate.strftime('%Y-%m-%d')
        secondthirdDate = secondthirdDate.strftime('%Y-%m-%d')
        thirdquarterDate = thirdquarterDate.strftime('%Y-%m-%d')
        endDate = endDate.strftime('%Y-%m-%d')

        if dateRange == 2:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, endDate))
            p1.start()
            p1.join()
        if dateRange == 3:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, middleDate))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, endDate))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        if dateRange == 4:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, middleDate))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, endDate))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        if dateRange == 5:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, middleDate))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, endDate))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        if dateRange == 6:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, firstthirdDate))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, firstthirdDate, secondthirdDate))
            p3 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, secondthirdDate, endDate))
            p1.start()
            p2.start()
            p3.start()
            p1.join()
            p2.join()
            p3.join()
        if dateRange == 7:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, firstthirdDate))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, firstthirdDate, secondthirdDate))
            p3 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, secondthirdDate, endDate))
            p1.start()
            p2.start()
            p3.start()
            p1.join()
            p2.join()
            p3.join()
        else:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, firstquarterDate))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, firstquarterDate, middleDate))
            p3 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, thirdquarterDate))
            p4 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, thirdquarterDate, endDate))
            p1.start()
            p2.start()
            p3.start()
            p4.start()
            p1.join()
            p2.join()
            p3.join()
            p4.join()

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
