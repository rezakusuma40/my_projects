# to run this program
# spark-submit --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.5.2,com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.27.1 spark_big_project.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, trim, lower
# from pyspark.sql.types import StructType, StructField, StringType # unused, for easy copy-paste
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound
from datetime import datetime, timedelta, date
import os
import re
import pytz

# Set the required environment variables
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "serviceaccount/belajar-bigdata-250ea8859e78.json"
os.environ["GOOGLE_CLOUD_PROJECT"] = "belajar-bigdata"

# get today datetime
now = datetime.now()
# Convert the datetime to the Asia/Jakarta timezone
tz = pytz.timezone("Asia/Jakarta")
now_jakarta = now.astimezone(tz)
# Get the date from the datetime object
date_jakarta = now_jakarta.date()
# get date of yesterday
one_day = timedelta(days=1)
yesterday = date_jakarta - one_day
ye_str_day=str(yesterday)

# Create a SparkSession
spark = SparkSession\
        .builder\
        .appName("Big Project Batch")\
        .master("local[*]") \
        .getOrCreate()

# Read the JSON files in the directory
df = spark.read.json(f"gs://big_project/investasi-{ye_str_day}")

df_chosen=df.select(
                col('id').alias('id'),
                col('created_at').alias('created_at'),
                col('user.screen_name').alias('user_name'),
                col('full_text').alias('tweet'),
                col('lang').alias('language'),
                )

df_filtered=df_chosen.filter(~lower(col("tweet")).like("%rt @%"))\
                    .filter("language == 'in'")

# UDF declaration
def cleanTweet(z):
    # remove links
    z=re.sub(r'http\S+', '', z)
    z=re.sub(r'bit.ly/\S+', '', z)
    z=z.strip('[link]')
    # remove users
#     z=re.sub('(RT\s@[A-Za-z]+[A-Za-z0-9-_]+)', '', z)
#     z=re.sub('(@[A-Za-z]+[A-Za-z0-9-_]+)', '', z)
    # remove emoticon
    z = re.sub(r'[\U0001F600-\U0001F64F]', '', z)
    # remove unicode
    z = z.encode('ascii', 'ignore').decode('ascii')
    # remove new line
    z = re.sub(r'\n+', '', z)
    # remove punctuations
    my_punctuation='!"$%&\'()*+,-./:;<=>?[\\]^_`{|}~•@â#'
    z=re.sub('['  +  my_punctuation  +  ']+', ' ', z)
    # remove hashtag
#     z=re.sub('(#[A-Za-z]+[A-Za-z0-9-_]+)', '', z)
    # remove multiple spaces
    z=re.sub(' +', ' ', z)
    return z
udf_tweet=udf(lambda z: cleanTweet(z))

df_clean=df_filtered.select(
                    col("id"),
                    col("created_at"),
                    col("user_name"),
                    udf_tweet(col("tweet")).alias("tweet"),
                    col("language"),
                    )\
                    .withColumn("tweet", trim(col("tweet")))

def getDatetime(y):
    y = datetime.strptime(y,'%a %b %d %H:%M:%S +0000 %Y').strftime('%Y-%m-%d %H:%M:%S')
    return y
get_datetime = udf(lambda z: getDatetime(z))

df_final=df_clean.withColumn("created_at", get_datetime("created_at").cast("timestamp"))

SERVICE_ACCOUNT_JSON=r'serviceaccount/belajar-bigdata-250ea8859e78.json'

# Construct a BigQuery client object.
client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_JSON)

# Set the project and dataset ID
project_id = "belajar-bigdata"
dataset_name = "bigproject"
ds_location = 'US'
table_name = "investasi"

def create_bigquery_dataset(dataset_name):
    dataset_id = "{}.{}".format(client.project, dataset_name)
    try:
        client.get_dataset(dataset_id)
        print("Dataset {} already exists".format(dataset_id))
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = ds_location
        dataset = client.create_dataset(dataset, timeout=60)
        print("Created dataset {}.{}".format(client.project, dataset.dataset_id))

create_bigquery_dataset(dataset_name)

# create table
query_job = client.query(
    f"""
    create table if not exists {project_id}.{dataset_name}.{table_name} 
    (
    id integer,
    created_at timestamp,
    user_name string,
    tweet string,
    language string
    )
    """
)
results = query_job.result()

# Set up the Google Cloud Storage client
client2 = storage.Client()

# Get a reference to the bucket where the file will be stored
BUCKET_NAME = 'tmp_big_project'

# Check if the bucket already exists
if not client2.lookup_bucket(BUCKET_NAME):
    # Create the bucket
    bucket = storage.Bucket(client2, name=BUCKET_NAME)
    bucket.create()
    print(f'Bucket {BUCKET_NAME} created')
else:
    print(f'Bucket {BUCKET_NAME} already exists')

# Write the DataFrame to BigQuery
df_final.write\
    .mode("append")\
    .format("bigquery") \
    .option("table", f'{project_id}.{dataset_name}.{table_name}') \
    .option("temporaryGcsBucket", BUCKET_NAME) \
    .save()

# Write data to elasticsearch
indexelk='investasi'
query2=df_final.write\
        .mode('append')\
        .format('org.elasticsearch.spark.sql')\
        .option('es.resource', indexelk)\
        .option('es.nodes','https://34.170.138.131')\
        .option('es.port','9200')\
        .option("es.index.auto.create", "true")\
        .save()