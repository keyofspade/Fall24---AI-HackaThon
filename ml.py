import pandas as pd
from azure.storage.blob import BlobServiceClient
from io import StringIO
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
from dotenv import load_dotenv

# Load environment variables
load_dotenv('language.env')

# Connection String
connection_string = os.getenv("connection_string")

# Create the BlobServiceClient object to interact with the blob service
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Name of container and blob file
container_name = "ingest-dashboard"
blob_name = "pii_detection_log.json"

# Get the BlobClient for the specific blob and download JSON data
blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
json_data = blob_client.download_blob().readall().decode('utf-8')

# Load the JSON data into a pandas DataFrame
data = pd.read_json(StringIO(json_data))

# Dictionary to map the existing category names in `data` to match the names in `recommendations_data`
category_mapping = {
    "Person": "PersonName",
    "DateTime": "DateOfBirth",
    "SWIFTCode": "BankAccountNumber",
    "PersonType": "PersonType",
    "Organization": "Organization",
    "USSocialSecurityNumber": "SSN",
    "Address": "PatientAddress",
    "Email": "Email",
    "CreditCardNumber": "CreditCardNumber",
    "PhoneNumber": "PhoneNumber",
    "UKNationalHealthNumber": "HealthPlanBeneficiaryNumber",
    "InternationalBankingAccountNumber": "BankAccountNumber",
    "IPAddress": "IP Address",
    "IDIdentityCardNumber": "ID Card Number",
    "EUDebitCardNumber": "CreditCardNumber",
    "Insurance Policy Number": "InsurancePolicyNumber",  
    "Medical Record Number": "MedicalRecordNumber"      
}

# Apply the mapping to the 'category' column in the data DataFrame
data['category'] = data['category'].map(category_mapping).fillna(data['category'])

# Recommendations as a list of dictionaries
recommendations_data = [
    {"category": "SSN", "Action": "Immediate Encryption", 
     "Recommendation": "Apply AES-256 encryption, separate from other data, and conduct regular access audits."},
    {"category": "Medical Record", "Action": "Immediate Encryption", 
     "Recommendation": "AES-256 encryption, comply with HIPAA, and perform regular access audits."},
    {"category": "Email", "Action": "Encryption and Masking", 
     "Recommendation": "Use TLS for transmission, AES-256 for storage, and implement MFA."},
    {"category": "Organization", "Action": "Encryption and Access Restriction", 
     "Recommendation": "Encrypt policy details and restrict access to authorized personnel."},
    {"category": "CreditCardNumber", "Action": "Encryption and Masking", 
     "Recommendation": "AES-256 encryption and tokenization; ensure PCI DSS compliance."},
    {"category": "BankAccountNumber", "Action": "Immediate Encryption", 
     "Recommendation": "Apply AES-256 encryption and limit access to authorized users."},
    {"category": "PhoneNumber", "Action": "Encryption and Access Restriction", 
     "Recommendation": "Encrypt and limit access to legitimate users; data minimization for non-essential usage."},
    {"category": "PatientAddress", "Action": "Encryption and Redaction", 
     "Recommendation": "Encrypt (AES-256), restrict access, and redact when sharing data."},
    {"category": "HealthPlanBeneficiaryNumber", "Action": "Immediate Encryption", 
     "Recommendation": "Apply encryption and implement RBAC; comply with identity protection laws."},
    {"category": "DateOfBirth", "Action": "Encryption and Redaction", 
     "Recommendation": "Encrypt and anonymize when unnecessary, and limit usage in public datasets."},
    {"category": "PersonName", "Action": "Redaction or Encryption", 
     "Recommendation": "Anonymize or pseudonymize; limit access under GDPR guidelines."},
    {"category": "PersonType", "Action": "Limited Access and Encryption", 
     "Recommendation": "Encrypt data and restrict access to legitimate users; comply with data protection regulations."},
    {"category": "IP Address", "Action": "Masking and Encryption", 
     "Recommendation": "Mask the last octet for reporting; encrypt data at rest and in transit."},
    {"category": "ID Card Number", "Action": "Immediate Encryption", 
     "Recommendation": "Apply AES-256 encryption, limit access to authorized personnel, and conduct regular audits."},
    {"category": "Insurance Policy Number", "Action": "Masking and Encryption", 
     "Recommendation": "Mask policy number details in reports and encrypt sensitive data; limit access."},  
    {"category": "Medical Record Number", "Action": "Masking and Encryption", 
     "Recommendation": "Mask medical record numbers in public datasets and apply AES-256 encryption."} 
]


# Convert recommendations list to DataFrame
recommendations_df = pd.DataFrame(recommendations_data)

# Define features and target columns in `data`
X = data[['source_document', 'entity', 'category', 'confidence_score', 'timestamp', 'compliance_tags', 'sensitive_type' ]]

# Split the data into training and testing sets (80% training, 20% testing)
X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)

# Merge `X_train` with `recommendations_df` on the `category` column
# to add `Action` and `Recommendation` for training
training_data = X_train.merge(recommendations_df, on='category', how='left')

def train_rf_classifier(training_data, target_column):
    # Check if the target column exists
    if target_column not in training_data.columns:
        raise ValueError(f"{target_column} is not a valid column in the training data.")
    
    # Label encode 'category' and the target variable to prepare for modeling
    training_data['category_encoded'] = LabelEncoder().fit_transform(training_data['category'])
    label_encoder = LabelEncoder()
    training_data['target_encoded'] = label_encoder.fit_transform(training_data[target_column])

    # Define features and target
    X = training_data[['confidence_score', 'category_encoded']]
    y = training_data['target_encoded']

    # Model Training
    rf_classifier = RandomForestClassifier(random_state=42)
    rf_classifier.fit(X, y)

    # Predictions
    y_pred = rf_classifier.predict(X)

    # Create a DataFrame for the predictions
    predictions_df = pd.DataFrame({
        'confidence_score': X['confidence_score'].values,
        'category_encoded': X['category_encoded'].values,
        'predicted_action': label_encoder.inverse_transform(y_pred)  # Decode the predicted actions
    })

    # Print the classification report
    print(f"Classification Report for {target_column}:\n", classification_report(y, y_pred))

    # Save the trained model
    joblib.dump(rf_classifier, f'rf_classifier_model_{target_column}.joblib')

    return predictions_df

# Train models for Action and Recommendation, storing predictions
action_predictions = train_rf_classifier(training_data, 'Action')
recommendation_predictions = train_rf_classifier(training_data, 'Recommendation')

# Ensure both prediction DataFrames have the same number of rows before adding the recommendation column
if len(action_predictions) == len(recommendation_predictions):
    # Add the recommendation predictions as a new column to the action predictions DataFrame
    action_predictions['predicted_recommendation'] = recommendation_predictions['predicted_action'].values
    
    # Rename columns for clarity
    action_predictions.columns = ['confidence_score', 'category_encoded', 'predicted_action', 'predicted_recommendation']
else:
    print("Error: The prediction DataFrames have different lengths.")


# Create a new DataFrame with relevant columns
relevant_columns = training_data[['entity', 'category', 'Action', 'Recommendation']].copy()

# Add action and recommendation predictions to the new DataFrame
relevant_columns['predicted_action'] = action_predictions['predicted_action'].values
relevant_columns['predicted_recommendation'] = action_predictions['predicted_recommendation'].values

# Prepare X_test DataFrame by handling unseen categories
category_encoder = LabelEncoder().fit(training_data['category'])
X_test['category_encoded'] = X_test['category'].apply(
    lambda x: category_encoder.transform([x])[0] if x in category_encoder.classes_ else -1
)

# Remove rows with unknown (-1) category encodings from the test set if necessary
X_test = X_test[X_test['category_encoded'] != -1]

# Define features for testing
X_test_features = X_test[['confidence_score', 'category_encoded']]

# Make predictions on the test set for Action
rf_classifier = joblib.load(f'rf_classifier_model_Action.joblib')  # Load the action model
action_encoder = LabelEncoder().fit(training_data['Action'])
action_test_predictions = rf_classifier.predict(X_test_features)

# Create a DataFrame for the action predictions
action_test_predictions_df = pd.DataFrame({
    'source_document': X_test['source_document'].values,
    'entity': X_test['entity'].values,
    'category': X_test['category'].values,
    'confidence_score': X_test['confidence_score'].values,
    'timestamp': X_test['timestamp'].values,
    'compliance_tags': X_test['compliance_tags'].values,
    'sensitive_type': X_test['sensitive_type'].values,
    'predicted_action': action_encoder.inverse_transform(action_test_predictions)
})

# Make predictions on the test set for Recommendation
rf_classifier_rec = joblib.load(f'rf_classifier_model_Recommendation.joblib')  # Load the recommendation model
recommendation_encoder = LabelEncoder().fit(training_data['Recommendation'])
recommendation_test_predictions = rf_classifier_rec.predict(X_test_features)

# Create a DataFrame for the recommendation predictions
recommendation_test_predictions_df = pd.DataFrame({
    'entity': X_test['entity'].values,
    'category': X_test['category'].values,
    'confidence_score': X_test['confidence_score'].values,
    'predicted_recommendation': recommendation_encoder.inverse_transform(recommendation_test_predictions)
})

# Combine both action and recommendation predictions into one DataFrame
final_test_predictions = action_test_predictions_df.merge(
    recommendation_test_predictions_df, on=['entity', 'category', 'confidence_score']
)

# Display the final predictions
final_test_predictions

# Save the final predictions DataFrame to a CSV file
final_test_predictions.to_csv('final_test_predictions.csv', index=False)
print("Final test predictions saved to 'final_test_predictions.csv'.")

final_test_predictions
blob_name_csv = 'ML-prediction.csv'

# Create a BlobClient for the new CSV file
blob_client_csv = blob_service_client.get_blob_client(container="ingest-dashboard", blob=blob_name_csv) # Changed where CSV is loaded

# Upload the CSV file
with open('final_test_predictions.csv', 'rb') as data:
    blob_client_csv.upload_blob(data, overwrite=True)  

print(f"Uploaded '{blob_name_csv}' to container 'ingest-dashboard' without overwriting.")
# print(f"Uploaded '{blob_name_csv}' to container '{container_name}' without overwriting.")
