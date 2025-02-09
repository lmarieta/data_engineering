from airflow import DAG
from airflow.providers.microsoft.azure.transfers.local_to_wasb import LocalFilesystemToWasbOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
from datetime import timedelta
import requests
import json

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
        price = data[0]["current_price"]
        if price:
            file_path = "/opt/airflow/data/bitcoin_price.json"  # Ensure this is a valid path inside your container
            with open(file_path, "w") as f:
                json.dump({"bitcoin_price": price}, f)
            
            print(f"Bitcoin Price: ${price} - Saved to {file_path}")
            return file_path  # Return the file path for the next task
        else:
            raise ValueError("Bitcoin price not found in response.")
    else:
        raise Exception(f"API request failed with status code {response.status_code}")

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
    schedule_interval='@once',
    catchup=False
) as dag:

    get_price_task = PythonOperator(
        task_id='fetch_bitcoin_price',
        python_callable=get_bitcoin_price,
    )

    upload_to_azure_task = LocalFilesystemToWasbOperator(
        task_id='upload_bitcoin_price_to_azure',
        file_path="/opt/airflow/data/bitcoin_price.json",  # Ensure the path matches the one used in `get_bitcoin_price`
        container_name='iubi-container',
        blob_name='bitcoin_price.json',
        wasb_conn_id='wasb_default'  # Ensure this matches your Airflow connection ID
    )

    get_price_task >> upload_to_azure_task