# Import necessary libraries
import os
from google.cloud import storage
from kafka import KafkaConsumer
from json import loads, dumps
from datetime import datetime, timedelta
import pytz

# Set the environment variable for the service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/rezakusuma40/serviceaccount/belajar-bigdata-f9d6805cd6a2.json"
os.environ["GOOGLE_CLOUD_PROJECT"] = "belajar-bigdata"

# Set up the Google Cloud Storage client
client = storage.Client()

# Get a reference to the bucket where the file will be stored
BUCKET_NAME = 'big_project'

# Check if the bucket already exists
if not client.lookup_bucket(BUCKET_NAME):
    # Create the bucket
    bucket = storage.Bucket(client, name=BUCKET_NAME)
    bucket.create()
    print(f'Bucket {BUCKET_NAME} created')
else:
    bucket = storage.Bucket(client, name=BUCKET_NAME)
    print(f'Bucket {BUCKET_NAME} already exists')

# Set up the Kafka consumer
topic = 'investasi'
consumer = KafkaConsumer(
    topic,
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',
    value_deserializer=lambda x: loads(x.decode('utf-8'))\
)

# writing data from kafka topic to files in compute engine streamingly, then move a file to cloud storage daily
# the files are headless csv with only 1 column, each row is a dictionary. the files contains all consumed tweets in 1 day
utc_tz = pytz.timezone('UTC')
jkt_tz = pytz.timezone('Asia/Jakarta')
one_day = timedelta(days=1)
for records in consumer:
    record_data = records.value
    created_at_str = record_data['created_at']
    ID_STR = record_data['id_str']
    created_at_utc_dt = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y').replace(tzinfo=utc_tz)
    created_at_jkt_dt = created_at_utc_dt.astimezone(jkt_tz)
    date = created_at_jkt_dt.date()
    DATE_STR = str(date)
    DIRECTORY_NAME = f'investasi-{DATE_STR}'
    # Get a reference to the directory where the file is stored
    directory = bucket.get_blob(f'{DIRECTORY_NAME}/')
    # If the directory doesn't exist, create it
    if not directory:
        directory = storage.Blob(f'{DIRECTORY_NAME}/', bucket)
        directory.upload_from_string('')
        print(f'Bucket {DIRECTORY_NAME} created')
    blob = bucket.blob(f'{DIRECTORY_NAME}/tweet-{ID_STR}.json')
    blob.upload_from_string(dumps(record_data))