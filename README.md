# 2024-AI-HACKATHON
# Team PawsitiveAI

This repository contains all necessary Python scripts and files to build AegisScan — a real-time tool for detecting and managing sensitive data, particularly PII (Personally Identifiable Information) and PHI (Protected Health Information). AegisScan is designed to support organizations in both the private and federal sectors by recommending best practices to ensure sensitive data is safeguarded, streamlining data management and compliance.

The product consists of the following main components:

1. `languagemodel`: Azure function app containing Python scripts to ingest raw files and automate calls to AI Language model and ML model.
2. `language.env`: Empty environmental file that you need to add your Azure credentials, URI, and API keys to run the Python scripts.
3. `ml.py`: Python script responsible for uploading from Azure storage account's blob container and running Random Forest Model to determine action/recommendation predictions.
4. `flask_app`:
   * `app.py`: Python script that contains Flask app that accepts file submission and transfers it to the azure blob storage.
   * `/templates` directory contains the html format(s)
   * `/static` contains static assets like CSS and JavaScript files for the web interface.
## Features
![alt text](https://github.com/keyofspade/Fall24---AI-HackaThon/blob/main/architecture_diagram.png)
* File Upload and Storage: Users upload files through the web app, which are stored in a designated Azure Blob Storage container.
* Automated Data Detection and Categorization:
    * A Logic App triggers an Azure Function workflow, analyzing files via the Azure Language Service to detect and categorize PII/PHI.
    * The ML model processes the output JSON to generate actionable recommendations.
    * The final output is saved as a CSV in Blob Storage, where PowerBI connects to retrieve and visualize insights via PowerBI, Tableau, etc.
* Data Visualization: PowerBI connects to the Blob Storage for ongoing insights and visualizations.

## Prerequisites

To run the Python scripts, ensure that you have the following prerequisites set up:

1. Python 3.x installed on your system. [Download Python](https://www.python.org/downloads/)
2. **Azure CLI** configuration. [Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-macos)
3. Required Python packages installed. You can install the necessary packages by running the following command in your terminal or command prompt. Be sure to set up an environment as necessary

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/keyofspade/Fall24---AI-HackaThon.git
    cd Fall24---AI-HackaThon
    ```

2. **Install Required Python Packages**:
    ```bash
    pip install python-dotenv azure-identity azure-storage-blob pandas scikit-learn joblib
    ```

## Usage
  
1. **Create and Update Environment Files**:
   - Fill in the provided environmental files with your Azure credentials and configurations.
   - Note: Ensure language.env is in .gitignore to keep credentials secure.
     
2. **Access the Web Interface**:
   - Open your web browser and navigate to the URL provided by the Flask server to access the product and submit your desired file.
  
3. **Connect PowerBI to Blob Storage**
   - To visualize insights

### Troubleshooting

If you encounter any issues during setup or usage, refer to the following troubleshooting tips:

1. **Azure CLI Configuration**: Ensure that your Azure CLI is properly configured with the correct subscription and permissions. You can verify this by running `az account show` in your terminal and checking that the correct subscription is active.

2. **Python Environment**: If you encounter errors related to missing packages or compatibility issues, double-check that you are using the correct Python environment. Consider using a virtual environment to isolate dependencies.

3. **Environmental File Configuration**: Check that your `language.env` files are correctly configured with the required Azure credentials, URI, and API keys. Any typos or incorrect formatting can lead to authentication failures.

4. **Web Interface**: If you are unable to access the web interface served by Flask, ensure that the Flask app is running correctly (`python flask_app/app.py`) and that there are no firewall or network restrictions blocking access to port 5000.

5. **Logging and Debugging**: Enable logging and debugging in your scripts to capture detailed information about any errors or issues encountered. This can help pinpoint the root cause of problems and facilitate troubleshooting.

By following these troubleshooting tips and leveraging community support, you should be able to resolve most issues encountered while setting up or using the AI Search solution.
## Acknowledgements

We extend our gratitude to [Women in Cloud](https://www.womenincloud.com/) and [Microsoft](https://www.microsoft.com) for organizing and hosting this Hackathon AI challenge. Their commitment to fostering diversity and innovation in the tech industry has provided us with a valuable opportunity to showcase our skills and develop impactful solutions. We appreciate their support and dedication to empowering individuals and communities through technology.
