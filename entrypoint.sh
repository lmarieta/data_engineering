#!/usr/bin/env bash

# Initialize the Airflow database (if necessary)
airflow db migrate

# Wait for Postgres to be ready
sleep 10

# create a user
airflow users create \
    --username airflow \
    --firstname lucas \
    --lastname m \
    --email lucas.marietan@hotmail.com \
    --role Admin \
    --password airflow

# Install required Python packages
echo "Installing Python dependencies..."
pip install -r /opt/airflow/requirements.txt

# Start the scheduler and webserver in the background
exec "$@"