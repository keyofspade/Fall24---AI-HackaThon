import requests
import json
import azure.functions as func

scoring_uri = "ML-model-service-uri"
api_key = "ML-primary-key"

def main(req: func.HttpRequest) -> func.HttpResponse:
    data = req.get_json()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    response = requests.post(scoring_uri, data=json.dumps(data), headers=headers)
    return func.HttpResponse(response.text, status_code=response.status_code)
