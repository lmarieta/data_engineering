# Stage 1: Use a base image to set the script permissions
FROM apache/airflow:2.10.2-python3.9 AS builder

# Copy the entrypoint script into the container and set permissions
USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Stage 2: Actual airflow image
FROM apache/airflow:2.10.2-python3.9

# Copy the entrypoint script from the builder stage
COPY --from=builder /entrypoint.sh /entrypoint.sh

# Set environment variables (if necessary)
ENV AIRFLOW_HOME=/opt/airflow

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for Airflow
CMD ["airflow", "webserver"]
