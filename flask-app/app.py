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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables.")
load_dotenv('language.env')

# Azure Blob Storage credentials
connection_string = os.getenv('connection_string')
container_name = os.getenv('container_name')

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
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part in the request.')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file.')
        return redirect(request.url)

    # Upload file to Blob Storage
    blob_client = container_client.get_blob_client(file.filename)
    blob_client.upload_blob(file, overwrite=True)
    flash('File uploaded successfully.')
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000) 

