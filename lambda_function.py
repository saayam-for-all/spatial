import serverless_wsgi
from app import app  # Import your Flask app object

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    This function acts as a bridge between API Gateway and Flask.
    """
    base_path_prefixes = [
        "/dev/spatial/v0.0.1",  # stage URL
        "/v1/spatial"  # custom domain URL
    ]

    for prefix in base_path_prefixes:
        if event["path"].startswith(prefix):
            event["path"] = event["path"][len(prefix):]
            break

    # Ensure path starts with "/"
    if not event["path"].startswith("/"):
        event["path"] = "/" + event["path"]


    return serverless_wsgi.handle_request(app, event, context)