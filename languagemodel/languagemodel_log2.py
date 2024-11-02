#Ensure environment has pip install azure-language 
# pip install azure-ai-textanalytics==5.2.0
# pip install azure-storage-file-datalake azure-identity
# pip install python-dotenv
# pip install azure-identity azure-storage-blob
# pip install PyPDF2
# pip install python-docx

"""Create storage and language model in the same instance. 
Configure "Storage Blob Constributor" and "Storage Account contributor" to users. Make sure container 
is in anonymous access and configuration allow anonymous access. 
Ran storage connection, and it seems to work with connection string"""

# Import libraries
import os
import sys
import re
import time
import json
import pandas as pd
import logging
from io import BytesIO
from azure.ai.textanalytics import TextAnalyticsClient 
from azure.core.credentials import AzureKeyCredential 
from azure.storage.blob import BlobServiceClient 
from dotenv import load_dotenv 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env file
logger.info("Loading environment variables.")
load_dotenv('language.env') 

# Read key variables
logger.info("Reading key variables from environment.")
connection_string = os.getenv('connection_string')
container_name = os.getenv('container_name')
container_nameML = os.getenv('container_nameML')
api_key = os.getenv('query_key')
endpoint = os.getenv('service_endpoint')

# Connect to the BlobServiceClient and textanalyticsclient
try:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    container_clientML = blob_service_client.get_container_client(container_nameML)
    logger.info("Blob Storage connected successfully.")
except Exception as e:
    logger.error(f"Failed to connect to Blob Storage: {str(e)}")
    raise

def authenticate_client():
    try:
        ta_credential = AzureKeyCredential(api_key)
        text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, credential=ta_credential
        )
        logger.info("Text Analytics client authenticated successfully.")
        return text_analytics_client
    except Exception as e:
        logger.error(f"Failed to authenticate Text Analytics client: {str(e)}")
        raise

client = authenticate_client()

def classify_compliance(sensitive_data_type):
    compliance_map = {
        'SSN': ['GDPR'],
        'USSocialSecurityNumber': ['GDPR'],
        'Medical Record': ['HIPAA'],
        'Email': ['GDPR'],
        'Insurance Policy': ['HIPAA'],  
        'CreditCardNumber': ['GDPR'],
        'BankAccountNumber': ['GDPR'],
        'PhoneNumber': ['GDPR', 'HIPAA'],
        'Address': ['HIPAA'],
        'HealthPlanBeneficiaryNumber': ['HIPAA'],
        'DateOfBirth': ['GDPR', 'HIPAA'],
        'Person': ['GDPR'],
        'IPAddress': ['GDPR'], 
        'Medical Record Number': ['HIPAA'],
        'Insurance Policy Number': ['HIPAA']
    }
    return compliance_map.get(sensitive_data_type, ['NA'])

def process_sensitive_data(detected_data):
    sensitive_info = detected_data['type']
    compliance_tags = classify_compliance(sensitive_info)

    if compliance_tags:
        print(f"Compliance tags for {sensitive_info}: {compliance_tags}")
    else:
        print(f"No compliance tags found for {sensitive_info}")

    return {
        'sensitive_data': detected_data['value'],
        'sensitive_type': sensitive_info,
        'compliance_tags': compliance_tags
    }

# Detect PII
def detect_pii(client, text, filename, domain="phi", confidence_threshold=0.8):
    records = []
    try:
        # Call the Azure PII entity recognition API
        pii_entities = client.recognize_pii_entities(documents=[text], domain_filter=domain)[0]
        
        if not pii_entities.entities:
            print("No PII/PHI entities detected in the text.")
        else:
            print(f"Detected {len(pii_entities.entities)} PII/PHI entities in the text.")
            
            for entity in pii_entities.entities:
                # Check if confidence threshold is met
                if entity.confidence_score >= confidence_threshold:
                    
                    print(f"Recognized entity: {entity.text} with category: {entity.category}")
                    
                    # Dict for the detected entity
                    detected_data = {
                        'type': entity.category,
                        'value': entity.text,
                    }
                    
                    # Process the sensitive data for compliance 
                    processed_record = process_sensitive_data(detected_data)
                    
                    # Log the processed record
                    records.append({
                        "source_document": filename,
                        "entity": processed_record['sensitive_data'],
                        "category": processed_record['sensitive_type'],
                        "confidence_score": entity.confidence_score,
                        "timestamp": pd.Timestamp.now().isoformat(),
                        "compliance_tags": processed_record['compliance_tags'],
                        "sensitive_type": "PHI" if domain == "phi" else "PII"
                    })
                else:
                    print(f"Entity '{entity.text}' skipped due to low confidence score: {entity.confidence_score}")

        # Define specific pattern for Medical Record Number and Policy Number
        mrn_pattern = re.compile(r'Medical Record Number:\s*([A-Z0-9]+)', re.IGNORECASE)
        policy_pattern = re.compile(r'Policy Number:\s*([A-Z0-9]+)', re.IGNORECASE)

        # Find matches for Medical Record Numbers
        mrn_matches = mrn_pattern.findall(text)
        print(f"MRN matches found: {mrn_matches}")  # Debug output
        for match in mrn_matches:
            detected_data = {
                'type': 'Medical Record Number',
                'value': match
            }
            processed_record = process_sensitive_data(detected_data)
            records.append({
                "source_document": filename,
                "entity": processed_record['sensitive_data'],
                "category": 'Medical Record Number',
                "confidence_score": 1.0,
                "timestamp": pd.Timestamp.now().isoformat(),
                "compliance_tags": processed_record['compliance_tags'],
            })

        # Find matches for Policy Numbers
        policy_matches = policy_pattern.findall(text)
        print(f"Policy matches found: {policy_matches}")  # Debug output
        for match in policy_matches:
            detected_data = {
                'type': 'Insurance Policy Number',
                'value': match
            }
            processed_record = process_sensitive_data(detected_data)
            records.append({
                "source_document": filename,
                "entity": processed_record['sensitive_data'],
                "category": 'Insurance Policy Number',
                "confidence_score": 1.0,
                "timestamp": pd.Timestamp.now().isoformat(),
                "compliance_tags": processed_record['compliance_tags'],
            })

    except Exception as e:
        print(f"Error detecting PII/PHI: {e}")

    return records

# Function to load existing records from Blob Storage JSON file
def load_existing_records(container_clientML, filename):
    try:
        blob_client = container_clientML.get_blob_client(filename)
        blob_data = blob_client.download_blob().readall()
        existing_records = json.loads(blob_data.decode("utf-8"))
        logging.info(f"Loaded existing records from {filename}")
    except Exception as e:
        logging.warning(f"No existing file found or error reading {filename}: {e}")
        existing_records = []   
    return existing_records

# Process files in Blob Storage and upload results
def process_files_in_blob_storage(container_client, container_clientML, client):
    # Load existing records from JSON file 
    output_filename = 'pii_detection_log.json'
    all_records = load_existing_records(container_clientML, output_filename)
    processed_files = {record["source_document"] for record in all_records}  # Set of processed files

    # Process each blob in container
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        if blob.name.endswith(".txt"):
            # Check if this blob file has already been processed
            if blob.name in processed_files:
                logging.info(f"Skipping already processed blob: {blob.name}")
                continue

            # Download and process new blob file
            blob_client = container_client.get_blob_client(blob.name)
            blob_data = blob_client.download_blob().readall()
            text = blob_data.decode("utf-8")
            logging.info(f"Processing new blob file: {blob.name}")
            new_records = detect_pii(client, text, blob.name)
            all_records.extend(new_records)  

    # Save updated JSON to another Blob Storage container
    try:
        blob_client = container_clientML.get_blob_client(output_filename)
        blob_client.upload_blob(BytesIO(json.dumps(all_records).encode('utf-8')), overwrite=True)
        logging.info(f"Uploaded updated results to blob storage: {output_filename}")
    except Exception as e:
        logging.error(f"Failed to upload updated results to blob storage: {e}")

# Run the processing
def main_process():
    # Initialize the processing
    process_files_in_blob_storage(container_client, container_clientML, client)
