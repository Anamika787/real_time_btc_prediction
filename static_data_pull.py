#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import requests
import json
import datetime
from tqdm import tqdm

# Coinbase API URL
base_url = 'https://api.coinbase.com/v2/prices/BTC-USD/spot?'

# Date Range for fetching data
sdate = datetime.date(2018,1,1)   # start date
today = datetime.datetime.today()
edate = datetime.date(today.year,today.month,today.day)   # end date
dates = pd.date_range(sdate,edate-datetime.timedelta(days=1),freq='d').strftime('%Y-%m-%d').tolist()

prices_df = pd.DataFrame(columns = ['Ticker','Date','Price'])
for date in tqdm(dates):
    date = str(date)

    # Modifying API URL to get prices of each day
    url = base_url + 'date=' + date
    
    # Fetching data from API
    response = requests.get(url)
    currencies = json.loads(response.text)
    
    # Processing the output
    price = float(currencies['data']['amount'])
    prices_df.loc[len(prices_df)] = ['BTC',date,price]
    
prices_df.head()
prices_df.to_csv('btc_price_history_daily.csv')


# In[ ]:


# Uploading data to MongoDB
get_ipython().system('pip install pymongo')


# In[ ]:


from pymongo import MongoClient
import pandas as pd
import urllib

mongo_uri = "mongodb+srv://manginaprabhat:mongodbpswd@cluster0.s1as72l.mongodb.net/?retryWrites=true&w=majority"

# Create a MongoDB client
client = MongoClient(mongo_uri)

try:
    client.admin.command('ping')
except Exception as e:
    print(f"Not connected - {e}")

# Connecting to MongoDB collection
db_name = "bitcoin"
cp_col_name = "closing_prices"
db = client.get_database(db_name)
collection = db.get_collection(cp_col_name)

# Updating data to MongoDB collection
prices_dict = prices_df.to_dict(orient='records')
collection.insert_many(prices_dict)


# In[ ]:




