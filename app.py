import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import time
from db_connection_1 import connect
from inference import fetch_prediction
import time
import matplotlib.pyplot as plt

# Coinbase API URL
COINBASE_API_URL = "https://api.coinbase.com/v2/prices"
format_string = "%Y-%m-%d"

# Function to get historical Coinbase data between a range of dates
def get_historical_data(df, start_time, end_time):
    df['Date'] = pd.to_datetime(df['Date'], format=format_string)
    df = df[(df['Date'] >= start_time) & (df['Date'] <= end_time)]
    return df

# Function to get historical Coinbase data for a certain day
def get_historical_data2(df, single_date):
    df['Date'] = pd.to_datetime(df['Date'], format=format_string)
    df = df[df['Date'] == single_date]
    return df

# Function to get historical Coinbase data for a certain day
def get_historical_data3(df, time):
    df['Date'] = pd.to_datetime(df['Date'], format=format_string)
    df = df[df['Date'] == single_date]
    return df

# Function to create trend plot --> price vs. date
def create_trend_plot(df, title):
    df.drop_duplicates(inplace=True, subset='Date')
    fig = px.line(df, x='Date', y='Price', title=title)
    return fig

# Function to create trend plot --> price vs. time
def create_detailed_trend_plot(df, title):
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time
    df.drop_duplicates(inplace=True, subset='Time')
    fig = px.line(df, x='Time', y='Price', title=title)
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='Price (USD)')
    return fig

# Function to get real-time Coinbase data
@st.cache_data(ttl=60)
def get_coinbase_data(coin_pair):
    url = f"{COINBASE_API_URL}/{coin_pair}/spot"
    response = requests.get(url)
    data = response.json()
    return data['data']['amount']

# Main Streamlit app
def main():

    
    # Dashboard title
    
    st.title(":blue[Real-Time Coinbase Data]")

    #Display current price of Bitcoin
    st.empty()
    with st.container(border=True):
      # st.title("Current Price")
      coin_pair = "BTC-USD"
      current_price = get_coinbase_data(coin_pair)
      cp1, cp2 = st.columns(2)
      # st.markdown(f":green[**Current {coin_pair} Price: ${current_price}**]")
      cp1.markdown(f"""<h5>Current {coin_pair} Price</h5>""",unsafe_allow_html=True)
      
      cp2.markdown(f"""<h5>${current_price}</h5>""",unsafe_allow_html=True)

      #Display predicted end-of-day price
      
      #Generate predictions from inference pipeline
      latest_pred, last_known_price = fetch_prediction()
      latest_pred = round(latest_pred,2)

      #Add red arrow if the predicted price is higher than the last known price
      if latest_pred>float(current_price):
        status = """<span style="color: red; font-size: 24px; font-weight: bold;">&#x2191;</span>"""
      #Add green arrow if the predicted price is lower than the last known price
      else:
        status =  """<span style="color: green; font-size: 24px; font-weight: bold;">&#x2193;</span>"""
      custom_style = """
      <style>
          .centered-text {
              text-align: left;
          }
          .custom-div {
              background-color: lightgray;
              opacity: 0.3;
              padding: 10px;
              border-radius: 5px;
          }
      </style>
      """

      # Render the custom style
      st.markdown(custom_style, unsafe_allow_html=True)

      p1, p2 = st.columns(2)
      #Display predicted price
      p1.markdown(f"""<h5 style='color: green;'>
          Predicted Closing Price</h5>
          """,unsafe_allow_html=True
      )
      p2.markdown(f"""<h5 style='color: green;'>${latest_pred} {status}</h5>
          """,unsafe_allow_html=True
      )

    # Get historical data for the last day, week, and month
    today = datetime.now()

    start_time_day = (today - timedelta(days=1)).strftime(format_string) #Calculate date 1 day ago
    start_time_week = (today - timedelta(days=7)).strftime(format_string) #Calculate date 1 week ago
    start_time_month = (today - timedelta(days=30)).strftime(format_string) #Calculate date 1 month ago
    start_time_year = (today - timedelta(days=365)).strftime(format_string) #Calculate date 1 year ago

    df = connect() #Fetch closing price data per day
    df_detailed = connect(detailed=True) #Fetch prices per 10 seconds
    #Format date and time columns
    df_detailed['Date'] = pd.to_datetime(df_detailed['Date'], format=format_string).dt.date
    df_detailed['Time'] = pd.to_datetime(df_detailed['Time'], format='%H:%M:%S').dt.time

    
    # Display Coinbase data over a certain period
    
    #Add title to this component
    st.title("View Coinbase data")

    # Date range selection
    start_date = st.date_input("Select start date", min_value=min(df['Date']), max_value=max(df['Date']), value=min(df['Date']))
    end_date = st.date_input("Select end date", min_value=min(df['Date']), max_value=max(df['Date']), value=max(df['Date']))

    # Filter DataFrame based on selected date range
    display_df = df[(df['Date'] >= start_date.strftime(format_string)) & (df['Date'] <= end_date.strftime(format_string))]

    # Display the selected date range
    st.write(f"Selected Date Range: {start_date.strftime(format_string)} to {end_date.strftime('%Y-%m-%d')}")
    #Format date  
    display_df['Date'] = display_df['Date'].dt.strftime(format_string)
    # Display the filtered DataFrame
    st.dataframe(display_df, hide_index=True, width=800)

    
    #Plot bar chart for evaluation metrics
    
    st.title("Model - Metrics")

    data = {'Model': ['Rolling Mean','Rolling Mean','Rolling Mean', 'Linear Rgression', 'Linear Rgression', 'Linear Rgression', 'Random Forest', 'Random Forest', 'Random Forest',
                      'Gradient Boost','Gradient Boost','Gradient Boost'],
            'Dataset': ["Train","Validation","Test","Train","Validation","Test","Train","Validation","Test","Train","Validation","Test"],
            'MAPE (%)': [5.01,4.21,2.75,2.97,3.05,1.87,2.27,30.07,21.06,3.2,39.41,29.66]}

    metric_df = pd.DataFrame(data)

    c3, c4,c5 = st.columns(3)

    c3.bar_chart(metric_df[metric_df["Dataset"]=="Train"],x="Model",y='MAPE (%)',color=["#FF0000"])
    c3.markdown(f"""<h5 style='text-align: center;'>Train Metrics</h5>""",unsafe_allow_html=True)
    
    c4.bar_chart(metric_df[metric_df["Dataset"]=="Validation"],x="Model",y='MAPE (%)',color=[ "#00FF00"])
    c4.markdown(f"""<h5 style='text-align: center;'>Validation Metrics</h5>""",unsafe_allow_html=True)

    c5.bar_chart(metric_df[metric_df["Dataset"]=="Test"],x="Model",y='MAPE (%)',color=["#0000FF"])
    c5.markdown(f"""<h5 style='text-align: center;'>Test Metrics</h5>""",unsafe_allow_html=True)
    
    #Plot Trends over different periods of time
    
    st.title("Trends")
  
    df_current = get_historical_data2(df_detailed,today.strftime(format_string)) 
    start_time_day = datetime.strptime(start_time_day, format_string)
    df_day = get_historical_data2(df_detailed, start_time_day.strftime(format_string)) 
    df_week = get_historical_data(df, start_time_week, today) 
    df_month = get_historical_data(df, start_time_month, today)
    df_year = get_historical_data(df, start_time_year, today)   

    #Display plots side by side
    col3, col4 = st.columns(2)
    col1, col2 = st.columns(2)

    col3.plotly_chart(create_detailed_trend_plot(df_current, "Stock Price trends today"),use_container_width=True)
    # if df_day.shape[0]>5:
    col4.plotly_chart(create_detailed_trend_plot(df_day, "Stock Price trends last day"),use_container_width=True)
    col1.plotly_chart(create_trend_plot(df_week, "Stock Price trends last week"),use_container_width=True)
    col2.plotly_chart(create_trend_plot(df_month, "Stock Price trends last month"),use_container_width=True)
    st.plotly_chart(create_trend_plot(df_year, "Stock Price trends last year"))    

    #Update dashboard every 1 minute
    while True:
      with st.spinner('Updating soon ...'):
        time.sleep(60)
      st.success('Updating!')
      st.experimental_rerun()


if __name__ == "__main__":
    main()
