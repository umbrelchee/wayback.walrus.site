from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
import os
import subprocess
from urllib.parse import urlparse, urlunparse
from datetime import datetime
from string import Template
import requests

print("Hey there! Walrus Wayback is starting!")
app = FastAPI()

# Define the directory for storing archives
ARCHIVE_DIR = "./archive"
BLOBS_DIR = "./blobs"

os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(BLOBS_DIR, exist_ok=True)

publisher_url = "https://publisher-devnet.walrus.space"

def upload_files_to_walrus(paths, publisher_url):
    urls = []
    for path in paths:
        with open(path, 'rb') as file_data:
            response = requests.put(f"{publisher_url}/v1/store", files={'file': file_data})
            print("Walrus response: ",path, response.status_code)
            if response.status_code == 200:
                blob_info = response.json()
                if "newlyCreated" in blob_info:
                    #urls.append(blob_info["newlyCreated"]["blobObject"]["id"])
                    urls.append(blob_info["newlyCreated"]["blobObject"]["blobId"])
                    print(f'Walrus info result {urls[-1]}')
                elif "alreadyCertified" in blob_info:
                    urls.append(blob_info["alreadyCertified"]["blobId"])
                    print(f'Walrus info result {urls[-1]}')
    return urls

from fastapi.staticfiles import StaticFiles

# Mount the 'static' directory to serve static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    # Serve the static 'index.html' file
    with open("frontend/index.html", "r") as file:
        return HTMLResponse(content=file.read(), status_code=200)

@app.get("/archives", response_class=JSONResponse)
async def get_archives(page: int = 1):
    files = [f for f in os.listdir(BLOBS_DIR)]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(BLOBS_DIR, x)), reverse=True)

    rows_per_page = 5
    start_index = (page - 1) * rows_per_page
    end_index = start_index + rows_per_page
    paginated_files = files[start_index:end_index]

    total_pages = (len(files) + rows_per_page - 1) // rows_per_page

    table_rows = []
    for filename in paginated_files:
        if ".html" in filename:
            continue
        path = os.path.join(BLOBS_DIR, filename)
        timestamp = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        with open(path, 'r') as file:
            real_name = file.read()

        url_display = remove_parentheses_content(real_name.replace("_", "/").replace(" ", ""))
        blob_url = f"https://aggregator-devnet.walrus.space/v1/{filename}"

        table_rows.append({
            "date": timestamp,
            "url": url_display,
            "blobUrl": blob_url
        })

    return {
        "rows": table_rows,
        "currentPage": page,
        "totalPages": total_pages
    }

import re

def remove_parentheses_content(input_string):
    # Use regex to replace all content within parentheses including the parentheses
    return re.sub(r'\(.*?\)', '', input_string)

@app.post("/archive", response_class=RedirectResponse)
async def archive_page(url: str = Form(...)):
    try:
        # Correct the URL and ensure HTTPS
        if not urlparse(url).scheme:
            url = 'https://' + url
        parsed_url = urlparse(url)
        path = parsed_url.path.strip("/")
        if not path:
            path = "index"
        filename = f"{parsed_url.netloc}_{path.replace('/', '_')}.html"

        # Run the SingleFile command to archive the URL
        archivebox_command = f"single-file --browser-executable-path=chromium-browser \"{url}\" {os.path.join(ARCHIVE_DIR, filename)}"
        subprocess.run(archivebox_command, shell=True, check=True)
        blob_ids = upload_files_to_walrus([os.path.join(ARCHIVE_DIR, filename)], publisher_url=publisher_url)
        print(blob_ids[0])
        with open(os.path.join(BLOBS_DIR, blob_ids[0]), 'w') as file:
            file.write(filename)
        # Redirect to the main page after archiving
        return RedirectResponse(url="/", status_code=303)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}", response_class=FileResponse)
async def get_file(filename: str):
    file_path = os.path.join(ARCHIVE_DIR, filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")
