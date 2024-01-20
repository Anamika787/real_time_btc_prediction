#spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.0 consumer.py
#pyspark --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0
from pyspark.sql.functions import *
from pyspark.sql import SparkSession

# Creating spark session
spark = SparkSession.builder.appName("bitcoin_time_series").getOrCreate()

# Reading streaming data
df=spark.readStream.format("kafka").option("kafka.bootstrap.servers", "localhost:9092").option("subscribe", "btc_prediction").option("startingOffsets", "earliest").load()

# Casting the data to readable format
newdf=df.selectExpr("CAST(value AS STRING)","CAST(timestamp AS STRING)")

# Writing it to json files
#query = newdf.writeStream.format("json").option('checkpointLocation','file:///home/ubuntu_vm/Desktop/checkpoint_bitcoin_temp/').option("path","file:///home/ubuntu_vm/Desktop/sparkfiles_temp/output_bitcoin_temp").outputMode('append').option('truncate','false').start()

# Writing it to MongoDB
query = newdf.writeStream \
    .outputMode("append") \
    .foreachBatch(lambda batch_df, batch_id:batch_df.write \
	    .format("mongo") \
	    .mode("append") \
	    .option("uri", "mongodb+srv://manginaprabhat:mongodbpswd@cluster0.s1as72l.mongodb.net/?retryWrites=true&w=majority") \
	    .option("database", "bitcoin") \
	    .option("collection", "temp_bitcoin") \
	    .option("replaceDocument", "false") \
	    .save()) \
    .start()
newdf.unpersist()

query.awaitTermination()
