# Importing necessary libraries
from kafka import KafkaProducer
import json
from data import application_user
import time
import requests
import json
import datetime

# Coinbase API URL
url = 'https://api.coinbase.com/v2/prices/BTC-USD/spot'

# Creating an instance of KafkaProducer
def ser_json(x):
    return json.dumps(x).encode('utf-8')
producer = KafkaProducer(bootstrap_servers=['localhost:9092'],value_serializer=ser_json)

# Executing the Producer
if __name__ == "__main__":
    i=0
    while True:

	# Fetching the data from Coinbase API
        response = requests.get(url)
        currencies = json.loads(response.text)	
        user = application_user(currencies)
        print(user)
        
        # Transferring the data
        producer.send('btc_prediction',user)
        i=i+1
        time.sleep(10)