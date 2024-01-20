from pymongo import MongoClient
import pandas as pd
import urllib
from datetime import datetime
import json 

format_string = "%Y-%m-%d"

def connect(detailed=False, viz=True):
    #Database URI for data stored in mongodb from Kafka
    mongo_uri = "mongodb+srv://manginaprabhat:mongodbpswd@cluster0.s1as72l.mongodb.net/?retryWrites=true&w=majority"    

    # Create a MongoDB client
    client = MongoClient(mongo_uri)

    #Check if connection is established
    try:
        client.admin.command('ping')
    except Exception as e:
        print(f"Not connected - {e}")

    db_name = "bitcoin" 
    collection_name = "temp_bitcoin" #Collection containing data per 10 seconds
    cp_col_name = "closing_prices" #Collection containing closing price of each day since 2018
    db = client.get_database(db_name)

    # Access a specific collection
    if detailed:
      collection = db.get_collection(collection_name)
    else:
      collection = db.get_collection(cp_col_name)

    #Find all documents in the collection
    cursor = list(collection.find())

    #Format data as per use
    if detailed:
      if viz:
        lst = format_detailed_data_viz(cursor)
      else:
        lst = format_detailed_data(cursor)
    else:
      lst = format_data(cursor)

    #Create dataframe with formatted data
    df = pd.DataFrame(lst)

    # Close the MongoDB connection
    client.close()
    return df

def format_data(cursor):
    lst = [{'Ticker':l["Ticker"], 'Date':datetime.strptime(l['Date'], format_string),'Price':l['Price']} for l in cursor]
    return(lst)

def format_detailed_data_viz(cursor):
    cursor = format_detailed_data(cursor)
    date_format = format_string
    time_format = "%H:%M:%S"
    lst = [{'Date':l["window"]['start'].strftime(date_format),'Time':l["window"]['start'].strftime(time_format),'Price':l["avg_amount"]} for l in cursor]
    return(lst)

def format_detailed_data(cursor):
    lst = format_intermediate(cursor)
    return(lst)

def parse_json(row):
    json_data = json.loads(row)
    return pd.Series([json_data['amount'], json_data['currency'], json_data['time']])

def combine_to_dict(row):
    return {'start': row['time_space_l'], 'end': row['time_space_u']}

def format_intermediate(raw_cursor):
  # Convert the list of dictionaries to a DataFrame
  temp = pd.DataFrame(raw_cursor)
  
  temp[['amount', 'currency', 'time']] = temp['value'].apply(parse_json)

  # type casting
  temp['time'] = pd.to_datetime(temp['time'])
  temp['amount'] = temp['amount'].astype(float)
  temp = temp[['_id','amount', 'currency', 'time']]
  # Dropping duplicate rows
  temp = temp.drop_duplicates()

  # calculating time columns for group by
  temp['time_space'] = temp['time'].dt.floor('1min')
  temp['time_space_l'] = temp['time'].dt.floor('1min')
  temp['time_space_u'] = temp['time'].dt.ceil('1min')
  windows_df = temp.groupby('time_space').agg({'amount': 'mean', 'time': 'count', 'time_space_l':'min', 'time_space_u':'min'}).rename(columns={'amount': 'avg_amount', 'time': 'cnt_timestamp'}).reset_index()
  windows_df = windows_df.sort_values(by='time_space')
  windows_df['time_space_l'] = pd.to_datetime(windows_df['time_space_l'])
  windows_df['time_space_u'] = pd.to_datetime(windows_df['time_space_u'])

  # calculating window column
  windows_df['window'] = windows_df.apply(combine_to_dict, axis=1)
  windows_df = windows_df.drop(columns= ['time_space','time_space_l','time_space_u'])

  return windows_df.to_dict(orient='records')