from flask import Flask, request, redirect, render_template, flash, url_for
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
import logging
import secrets

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generates a random 32-character hex string

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables.")
load_dotenv('language.env')

# Azure Blob Storage credentials
connection_string = os.getenv('connection_string')
container_name = os.getenv('container_name')

# Log loaded environment variables (mask sensitive data in production)
logger.debug(f"Connection String Loaded: {'Yes' if connection_string else 'No'}")
logger.debug(f"Container Name: {container_name}")

# Initialize BlobServiceClient
try:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    logger.info("Blob Storage connected successfully.")
except Exception as e:
    logger.error(f"Failed to connect to Blob Storage: {str(e)}")
    raise

@app.route('/')
def home():
    logger.info("Rendering home page (upload.html)")
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info("Received file upload request.")

    if 'file' not in request.files:
        logger.warning("No file part in the request.")
        flash('No file part in the request.')
        return redirect(request.url)

    file = request.files['file']
    logger.debug(f"Uploaded file name: {file.filename}")

    if file.filename == '':
        logger.warning("No file selected for upload.")
        flash('No selected file.')
        return redirect(request.url)

    # Upload file to Blob Storage
    try:
        blob_client = container_client.get_blob_client(file.filename)
        logger.info(f"Uploading file '{file.filename}' to Blob Storage.")
        blob_client.upload_blob(file, overwrite=True)
        flash('File uploaded successfully.')
        logger.info(f"File '{file.filename}' uploaded successfully.")
    except Exception as e:
        logger.error(f"Error uploading file '{file.filename}': {str(e)}")
        flash('Failed to upload file.')

    return redirect('/')

if __name__ == "__main__":
    logger.info("Starting Flask app on http://0.0.0.0:8000")
    app.run(debug=True, host="0.0.0.0", port=8000)

