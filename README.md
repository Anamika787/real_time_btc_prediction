# CS532 Final Project: Real-time end-of-day price prediction and analysis for bitcoin 

Our project consists of four major parts:

## Part 1: Obtaining live streaming data

We use Apache Kafka and Zookeeper to obtain the prices of bitcoin from Coinbase API. The following steps need to be followed to replicate the data ingestion segment.

1. Starting all the Hadoop deamons
```
start-all.sh
```

2. Starting the Spark deamons - Navigate to your $SPARK_HOME before executing these commands.
```
./sbin/start-master.sh
./sbin/start-worker.sh spark://localhost:8080
```
Execute jps command to see if hadoop and spark daemons were properly started
```
jps
```

3. Start zookeeper - Navigate to Kafka directory before executing these commands
```
sudo systemctl daemon-reload
sudo systemctl enable zookeeper
sudo systemctl start zookeeper
sudo systemctl status zookeeper
``` 
You should be seeing that zookeeper is active and running. If you see a failed message, it means that zookeeper is not configured properly in the system.

4. Start Kafka - Open a new terminal window and navigate to Kafka directory before executing these commands
```
sudo systemctl daemon-reload
sudo systemctl enable kafka
sudo systemctl start kafka
sudo systemctl status kafka
``` 
You should be seeing that Kafka is active and running. If you see a failed message, it means that kafka is not configured properly in the system.

5. Create a new kafka topic - Open a new terminal window and navigate to Kafka directory before executing these commands
```
bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1 --topic btc_prediction
```
You should be seeing an output which says "Created topic btc_prediction"

6. Listing active kafka topics - List the active kafka topics to verify if the topic is created
```
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

7. Run the producer file to extract data from Coinbase API - Navigate to the folder where the producer python file is located. Ensure that the 'producer.py' file has the same topic name as the topic we just created.
```
python3 producer.py
```
You should be seeing the current prices of bitcoin being displayed on the terminal for every 10 seconds.

8. Running the consumer - Navigate to the folder where the consumer python file is located. Ensure that the 'consumer.py' file has the same topic name as the topic we just created. Ensure that the 'consumer.py' file has the same 
```
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.0 --num-executors 1 --driver-memory 512m --executor-memory 1024m --executor-cores 1 consumer.py
```


## Part 2: Creating a PySpark Model Pipeline
We use a static dataset consisting of the end-of-day prices of bitcoin for every day to create the predictive model. We used the prices of bitcoin since 2018 for this analysis. Since this is a Time Series data, we took the first four years (roughly) as our training data. We then took the next 10 months (roughly) as our validation data and the data since as the testing data. After fetching the data, we created a PySpark Model using this data. This model is saved as a pyspark pipeline for deployment purposes. This pipeline is then used to make predictions on the live data. The following steps elaborate on this.

1. Creating a static dataset of end-of-day bitcoin prices since 2018

 Navigate to the folder where 'static_data_pull.py' file is present. This file automatically uploads the fetched data to a collection on MongoDB everytime it is run.
```
python3 static_data_pull.py
```

2. [OPTIONAL] 

Since, PySpark doesn`t have native Time Series models, we are utilizing the regression models to create the model. We processed the data and engineered new features like lag, rolling means, calendar features to create a regression model. The code is available in the 'BTC_Pyspark_Model.ipynb' notebook and 'btc_pyspark_model.py' file. There is no need to run the file, unless you want to train a new model. We have already included our final model in the form of a zip file in the submission. The zip file can be used to get the final predictions. However, if this code is being executed, care must be taken to change the paths appropriately inside the codes.

## Part 3: Obtaining the predictions on live data based using the saved model
1. Unzip the model.zip file in the working folder. The unzipped folder will have the details of the PySpark pipeline.
2. The inference.py file will be used to run the Pyspark pipeline and fetch the end of the day price predictions. The file includes steps to get the real-time data in the required format and perform data pre-processing steps similar to the training pipeline. The data is then passed to the loaded model to fetch the final results. 

The end-of-day results are displayed on the visulaization dashboard (described in part 4).

## Part 4: Analysis and visualization of the live data on Streamlit dashboard
We have created a streamlit dashboard to visualize the data and its trends, along with the end-of-day price predictions. The plots and predictions are updated every 1 minute to give the user the lastest information and insights. The following steps need to be followed to deploy the dashboard. They can be easily executed from the streamlit_deployment.ipynb file.  

1. Install the localtunnel package using npm (Node Package Manager)
```
!npm install localtunnel
```
2. Runs the Streamlit app - app.py, which contains the code for different components of the dashboard
```
!streamlit run app.py --server.maxUploadSize 600 &>/content/logs.txt &
```
.
This helps you to fetch the public IPv4 address of the machine where the code is running. This command is not directly related to Streamlit or localtunnel but might be used to check the public IP address. Note this public IP address for the next step.

3. Expose Streamlit app with public URL

--port 8501 specifies that the localtunnel should expose the local server running on port 8501 (default port for Streamlit). This generates a public URL that allows others to access and interact with the Streamlit app remotely
```
!npx localtunnel --port 8501
```
