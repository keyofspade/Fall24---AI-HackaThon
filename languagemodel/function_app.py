import logging
import azure.functions as func
from languagemodel_log2 import main_process  

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="GetLanguage") #Cannot change function name without erroring on write blob permisison
def GetLanguage(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Azure Function 'GetLanguage' triggered.")

    try:
        # Call the main process function to execute your logic
        main_process()

        return func.HttpResponse(
            "PII detection processing completed successfully.",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error occurred during PII processing: {str(e)}")
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )

