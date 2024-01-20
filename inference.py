from pyspark.sql import SparkSession
from pyspark.sql import functions as f
from pyspark.sql.window import Window
from pyspark.ml import PipelineModel

from db_connection_1 import connect
import pandas as pd
import os

#Generate rolling mean
def rolling_mean(df, days = 7):
  rolling_window = Window.orderBy("Date").rowsBetween(-(days), -1)
  df_new = df.withColumn(
  f"rolling_mean_{days}",f.avg("Price").over(rolling_window))
  return df_new

#Generate lag features
def lag_feature(df, lag_days):
  window_spec = Window.orderBy("Date")
  df_new = df.withColumn(f"Price_lag_{lag_days}", f.lag("Price", lag_days).over(window_spec))
  return df_new

#Feature engineering pipeline
def gbt_feature_eng(df):
  # Extracting day, month, week, and year
  df_new = df.withColumn("day", f.dayofmonth("Date")) \
  .withColumn("month", f.month("Date")) \
  .withColumn("week", f.weekofyear("Date")) \
  .withColumn("year", f.year("Date"))
  # Creating rolling mean columns
  days_list = [1,2,3,7,14,30,45,60]
  for days in days_list:
    df_new = rolling_mean(df_new, days)
    df_new = lag_feature(df_new, days)
  return df_new

def fetch_prediction():
    #Fetch data from database
    df = connect(detailed=True, viz=False)
    # Create a SparkSession
    spark = SparkSession.builder.appName("ExampleApp").getOrCreate()

    loaded_model = PipelineModel.load(os.getcwd()+os.sep+"content"+os.sep+"btc_model4.pkl")
    if "_id" in df.columns:
      df = df.drop(columns = ['_id'])
    
    split_df = pd.DataFrame(df['window'].apply(pd.Series))
    
    df_new = pd.concat([df, split_df], axis=1)
    numeric_col1 = df_new['start'].astype(int)
    numeric_col2 = df_new['end'].astype(int)
    mean_numeric = (numeric_col1 + numeric_col2) / 2
    df_new['mid'] = pd.to_datetime(mean_numeric)
    df_new_s = spark.createDataFrame(df_new)
    df_new_s = df_new_s.withColumn("window", f.to_timestamp("mid"))
    df_new_s = df_new_s.withColumnRenamed('window','Date').withColumnRenamed('avg_amount','Price').drop('cnt_timestamp')
    df_new_s = df_new_s.withColumn('Ticker',f.lit('BTC')).select('Ticker','Date','Price')
    #Pass data through data pre-processing pipeline
    df_new_fe = gbt_feature_eng(df_new_s)
    #Pass pre-processed data through the model to get predictions
    df_new_pred = loaded_model.transform(df_new_fe)

    df_pd = df_new_pred.toPandas()
    #Fetch predictions
    latest_price = df_pd['prediction'].iloc[-1]
    #Fetch last known data
    last_known_price = df_pd['Price'].iloc[-1]
    return latest_price, last_known_price