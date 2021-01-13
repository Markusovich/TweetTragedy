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
from flask_sqlalchemy import SQLAlchemy
import glob
import os
from dateutil.parser import parse
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__, static_url_path='/static')


for f in glob.glob('/static/*'):
    os.remove(f)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Link to Simon's database in mongodb atlas
MONGO_HOST = 'mongodb+srv://markusovich:Alexmom99@cluster0.enna3.mongodb.net/twitterdb?retryWrites=true&w=majority'
# Created a database named "twitterdb" in custer0
client = MongoClient(MONGO_HOST)
db = client.twitterdb

CONSUMER_KEY = "VqwMxvejCenz6f7agImTtyi0z"
CONSUMER_SECRET = "JwEIf2ZIgmbEFOuXulpg8erDaYX1F0QTddlmR1UID8VS04hjAA"
ACCESS_TOKEN = "1345892197816819712-H3Kx5dEXSawQDiTRu9xUaNF82lJhT6"
ACCESS_TOKEN_SECRET = "Zg2CG6eGVAt917vqqoAQu3Hdl1O1uUnoxmwDKbkj4jd7Q"

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

def plot_df(df, x, y, title="", xlabel='Date', ylabel='Tweets per date'):
    plt.figure()
    plt.bar(x, y)
    plt.gca().set(title=title, xlabel=xlabel, ylabel=ylabel)
    plt.savefig('static/timeseries.png')

def convertDate(jsonDate):
    new_datetime = datetime.strftime(datetime.strptime(
        jsonDate, '%a %b %d %H:%M:%S +0000 %Y'), '%Y-%m-%d')
    return new_datetime


def get_tweets(searchWord, locationName, date1, date2, count):

    searchWord += " -filter:retweets" + " -filter:replies"

    # Collect tweets
    tweets = tw.Cursor(api.search,
                       q=searchWord,
                       result="popular",
                       lang="en",
                       since=date1,
                       until=date2).items(count)

    flag = 0
    # Iterate and print tweets
    for tweet in tweets:
        flag = 0
        if locationName:
            try:
                if locationName in tweet._json['user']['location'] and flag == 0:
                    if model_prediction(tweet._json['text']):
                        print('pass')
                        db.tweetDB.insert_one({ "created_at": convertDate(tweet._json['created_at']), "text": tweet._json['text'], "location": tweet._json['user']['location']})
                        print('pass')
                        flag = 1
                if locationName in tweet._json['place']['country'] and flag == 0:
                    if model_prediction(tweet._json['text']):
                        print('pass')
                        db.tweetDB.insert_one({ "created_at": convertDate(tweet._json['created_at']), "text": tweet._json['text'], "location": tweet._json['place']['country']})
                        print('pass')
                        flag = 1
                if locationName in tweet._json['place']['name'] and flag == 0:
                    if model_prediction(tweet._json['text']):
                        print('pass')
                        db.tweetDB.insert_one({ "created_at": convertDate(tweet._json['created_at']), "text": tweet._json['text'], "location": tweet._json['place']['name']})
                        print('pass')
                        flag = 1
                else:
                    pass
            except TypeError:
                pass
        else:
            if model_prediction(tweet._json['text']):
                db.tweetDB.insert_one({ "created_at": convertDate(tweet._json['created_at']), "text": tweet._json['text']})

            
# prevent cached responses
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':

        db.tweetDB.remove({})

        disasterName = request.form['searchDisaster']
        locationName = request.form['searchLocation']
        dateRange = request.form['daterange']

        f = open('searchQueryRecords.txt', 'a')
        if locationName:
            f.write("Search for " + disasterName + " in " +
                    locationName + " for the last " + dateRange + " days.\n")
        else:
            f.write("Search for " + disasterName +
                    " for the last " + dateRange + " days.\n")
        f.close()

        beginDate = datetime.today() - timedelta(days=int(dateRange))
        endDate = datetime.today()
        firstquarterDate = beginDate + (endDate - beginDate)/4
        firstthirdDate = beginDate + (endDate - beginDate)/3
        middleDate = beginDate + (endDate - beginDate)/2
        secondthirdDate = beginDate + (endDate - beginDate)/3 * 2
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
                disasterName, locationName, beginDate, endDate, 1000))
            p1.start()
            p1.join()
        if dateRange == 3:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, middleDate, 500))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, endDate, 500))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        if dateRange == 4:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, middleDate, 500))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, endDate, 500))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        if dateRange == 5:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, middleDate, 500))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, endDate, 500))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        if dateRange == 6:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, firstthirdDate, 333))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, firstthirdDate, secondthirdDate, 333))
            p3 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, secondthirdDate, endDate, 333))
            p1.start()
            p2.start()
            p3.start()
            p1.join()
            p2.join()
            p3.join()
        if dateRange == 7:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, firstthirdDate, 333))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, firstthirdDate, secondthirdDate, 333))
            p3 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, secondthirdDate, endDate, 333))
            p1.start()
            p2.start()
            p3.start()
            p1.join()
            p2.join()
            p3.join()
        else:
            p1 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, beginDate, firstquarterDate, 250))
            p2 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, firstquarterDate, middleDate, 250))
            p3 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, middleDate, thirdquarterDate, 250))
            p4 = multiprocessing.Process(target=get_tweets, args=(
                disasterName, locationName, thirdquarterDate, endDate, 250))
            p1.start()
            p2.start()
            p3.start()
            p4.start()
            p1.join()
            p2.join()
            p3.join()
            p4.join()

        plt.rcParams.update({'figure.figsize': (10, 7), 'figure.dpi': 120})

        freq = {}
        for item in db.tweetDB.find( {} ):
            item['created_at']
            if (item['created_at'] in freq):
                freq[item['created_at']] += 1
            else:
                freq[item['created_at']] = 1

        data = []
        done = []
        for item in db.tweetDB.find( {} ):
            if item in done:
                pass
            else:
                data.append([item['created_at'], freq[item['created_at']]])
                done.append(item['created_at'])
        df = pd.DataFrame(data, columns=['date', 'value'])


        i = 7
        counter = datetime.today() - timedelta(days=int(i))
        counter = "'" + counter.strftime('%Y-%m-%d') + "'"
        today = "'" + datetime.today().strftime('%Y-%m-%d') + "'"

        while counter != today:
            if df['date'].str.contains(counter).any():
                pass
            else:
                df2 = pd.DataFrame([[counter, 0]], columns=['date', 'value'])
                df = df.append(df2, ignore_index=True)
            i = i - 1
            counter = datetime.today() - timedelta(days=int(i))
            counter = "'" + counter.strftime('%Y-%m-%d') + "'"

        df['date'] = pd.to_datetime(df['date'])

        plot_df(df, x=df['date'], y=df.value, title='Time Series Visualization')

        all_tweets = db.tweetDB.find( {} )
        tweetTitle = 'Tweets that may provide info to current disaster state'

        return render_template('home.html', all_tweets=all_tweets, tweetTitle=tweetTitle)
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