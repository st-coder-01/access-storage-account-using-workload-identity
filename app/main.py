import os
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Retrieve the storage blob service URL from environment variables
storage_url = os.environ["AZURE_STORAGE_BLOB_URL"]

if not storage_url:
    raise EnvironmentError("AZURE_STORAGE_BLOB_URL is not set in the environment variables")

try:
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=storage_url, credential=credential)

    logger.info("Successfully fetched the credential.")
except Exception as e:
    logger.error(f"Failed to fetch the credential: {e}")
    raise

@app.get("/")
async def hello():
    return {"message": "Hello World"}

@app.get("/read")
async def root():
    try:
        logging.info("Starting upload file process with storage URL: %s", storage_url)

        container_name="blob-container-01"
        container_client = blob_service_client.get_container_client(container=container_name)
        logging.info("Container client created successfully")

        # List blobs in the specified container
        blob_list = container_client.list_blobs()
        logging.info("blob_list: %s", blob_list)

        # Read and return the content of each blob
        blob_contents = {}
        for blob in blob_list:
            blob_client = container_client.get_blob_client(blob=blob.name)
            content = blob_client.download_blob().readall().decode('utf-8')
            blob_contents[blob.name] = content

        logging.info("Blob contents retrieved successfully")
        return {"blobs": blob_contents}

    except Exception as e:
        raise HTTPException(status_code=501, detail=str(e))
    
@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    try:
        container_name = "blob-container-02"
        container_client = blob_service_client.get_container_client(container=container_name)

        # Ensure the container exists
        if not container_client.exists():
            container_client.create_container()
            logger.info(f"Container {container_name} created successfully")
        
        # Generate a unique blob name using the uploaded file's filename
        blob_name = file.filename
        
        # Create a BlobClient
        blob_client = container_client.get_blob_client(blob=blob_name)
        
        # Upload the file to the blob
        blob_client.upload_blob(file.file, overwrite=True)
        
        logger.info(f"File {file.filename} uploaded successfully to {container_name}/{blob_name}")
        return {"filename": file.filename, "status": "File uploaded successfully"}
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=501, detail=str(e))