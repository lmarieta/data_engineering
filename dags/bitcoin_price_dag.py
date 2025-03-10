from airflow import DAG
from azure.storage.blob import BlobServiceClient
from airflow.operators.python import PythonOperator
from datetime import datetime
from datetime import timedelta
import requests
import csv
import os
from dotenv import load_dotenv  # Load environment variables

# Load .env variables
load_dotenv()
# Load .env variables
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_CONTAINER_NAME = os.getenv('AZURE_CONTAINER_NAME')
AZURE_BLOB_NAME = os.getenv('AZURE_BLOB_NAME')
LOCAL_FILE_PATH = "/opt/airflow/data/bitcoin_price.csv"

# Function to fetch Bitcoin price
def get_bitcoin_price():
    API_KEY = "CG-vdPsV15oqA92BzZjzFBfvSkM"  # Replace with your actual API key
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "ids": "bitcoin",
        "vs_currency": "usd",
        "x_cg_demo_api_key": API_KEY  # Include API key in request
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        date = datetime.now().isoformat()
        price = data[0]["current_price"]

        if price:
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(LOCAL_FILE_PATH), exist_ok=True)
                
                # Open file in append mode
                with open(LOCAL_FILE_PATH, "a", newline='') as f:
                    writer = csv.writer(f)
                    
                    # If the file doesn't exist, create it and write the header
                    if not os.path.exists(LOCAL_FILE_PATH) or os.stat(LOCAL_FILE_PATH).st_size == 0:
                        writer.writerow(["date", "bitcoin_price"])  

                    # Append new row with date and price
                    writer.writerow([date, price])

                print(f"✅ Bitcoin price {price} recorded at {date}")
                return LOCAL_FILE_PATH  # ✅ Ensure the file path is returned
            except Exception as e:
                raise Exception(f"Error writing to CSV: {e}")
        else:
            raise ValueError("Bitcoin price not found in response.")
    else:
        raise Exception(f"API request failed with status code {response.status_code}")

def upload_to_azure():
    try:
        # Create BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(AZURE_BLOB_NAME)

        # Open and upload file
        with open(LOCAL_FILE_PATH, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)  # ✅ Overwrite enabled

        print(f"✅ File '{LOCAL_FILE_PATH}' uploaded as '{AZURE_BLOB_NAME}'")
    except Exception as e:
        print(f"❌ Error uploading to Azure: {e}")

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 7),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'bitcoin_price_dag',
    default_args=default_args,
    schedule_interval=timedelta(minutes=5),#'@once',
    catchup=False
) as dag:

    get_price_task = PythonOperator(
        task_id='fetch_bitcoin_price',
        python_callable=get_bitcoin_price,
    )

    """     upload_to_azure_task = LocalFilesystemToWasbOperator(
        task_id='upload_bitcoin_price_to_azure',
        file_path="/opt/airflow/data/bitcoin_price.csv",  # Ensure the path matches the one used in `get_bitcoin_price`
        container_name='iubi-container',
        blob_name='bitcoin_price.csv',
        wasb_conn_id='wasb_default',  # Ensure this matches your Airflow connection ID
    ) """
    upload_to_azure_task = PythonOperator(
        task_id='upload_bitcoin_price_to_azure',
        python_callable=upload_to_azure,
    )

    get_price_task >> upload_to_azure_task