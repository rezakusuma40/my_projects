from google.cloud import bigquery

SERVICE_ACCOUNT_JSON=r'serviceaccount/belajar-bigdata-250ea8859e78.json'

# Construct a BigQuery client object.
client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_JSON)

# Set the project and dataset ID
dataset_name = "bp_datamart"
ds_location = 'US'

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

# create tables
query_job1 = client.query(
    """
    CREATE OR REPLACE TABLE belajar-bigdata.bp_datamart.total_tweet AS
    SELECT COUNT(*) total_tweet FROM belajar-bigdata.bigproject.investasi   
    """
)
results = query_job1.result()

query_job2 = client.query(
    """
    CREATE OR REPLACE TABLE belajar-bigdata.bp_datamart.total_tweet_per_keyword AS (
        SELECT 'saham' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(LOWER(tweet), r'saham')
        UNION ALL
        SELECT 'reksadana' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(LOWER(tweet), r'reksadana')
        UNION ALL
        SELECT 'sukuk' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(LOWER(tweet), r'sukuk')
    )
    """
)
results = query_job2.result()

query_job3 = client.query(
    """
    CREATE OR REPLACE TABLE belajar-bigdata.bp_datamart.total_tweet_daily_per_keyword AS (
        SELECT DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) date, 'saham' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(tweet, r'(?i)saham')
        AND DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) NOT IN ('2022-12-28')
        GROUP BY date
        UNION ALL
        SELECT DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) date, 'reksadana' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(tweet, r'(?i)reksadana')
        AND DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) NOT IN ('2022-12-28')
        GROUP BY date
        UNION ALL
        SELECT DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) date, 'sukuk' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(tweet, r'(?i)sukuk')
        AND DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) NOT IN ('2022-12-28')
        GROUP BY date
    )
    """
)
results = query_job3.result()

query_job4 = client.query(
    """
    CREATE OR REPLACE TABLE belajar-bigdata.bp_datamart.total_tweet_hourly_per_keyword AS (
        SELECT EXTRACT(HOUR FROM TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) hour, 'saham' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(LOWER(tweet), r'saham')
        AND DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) NOT IN ('2022-12-28')
        GROUP BY hour
        UNION ALL
        SELECT EXTRACT(HOUR FROM TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) hour, 'reksadana' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(LOWER(tweet), r'reksadana')
        AND DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) NOT IN ('2022-12-28')
        GROUP BY hour
        UNION ALL
        SELECT EXTRACT(HOUR FROM TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) hour, 'sukuk' keyword, COUNT(*) total
        FROM belajar-bigdata.bigproject.investasi
        WHERE REGEXP_CONTAINS(LOWER(tweet), r'sukuk')
        AND DATE(TIMESTAMP_ADD(created_at, INTERVAL 7 HOUR)) NOT IN ('2022-12-28')
        GROUP BY hour
    )
    """
)
results = query_job4.result()

query_job5 = client.query(
    """
    CREATE OR REPLACE TABLE belajar-bigdata.bp_datamart.most_active_user AS
    SELECT user_name, COUNT(*) total_tweet, RANK() OVER (ORDER BY COUNT(*) DESC) rank
    FROM belajar-bigdata.bigproject.investasi
    GROUP BY user_name
    HAVING COUNT(*) > 1
    ORDER BY total_tweet DESC
    LIMIT 10;
    """
)
results = query_job5.result()

