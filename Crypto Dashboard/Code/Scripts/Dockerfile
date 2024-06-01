FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install required packages
RUN pip3 install -r requirements.txt

# Copy the Python script into the container at /app
COPY crypto_dashboard.py /app/crypto_dashboard.py

# Expose port 8501
EXPOSE 8501

# Set the entrypoint to streamlit and specify the target Python script
ENTRYPOINT ["streamlit", "run"]

# Specify the target Python script for Streamlit
CMD ["crypto_dashboard.py"]
