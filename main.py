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

# HTML Template for the main page
HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Walrus Wayback Machine</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f8f9fa;
            color: #212529;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            max-width: 900px;
            width: 100%;
            background: #fff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            margin: 20px;
        }
        h1 {
            color: #007bff;
            font-size: 2.5em;
            margin-bottom: 20px;
            text-align: center;
        }
        .logo {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        .logo .walrus {
            font-size: 3em;
            color: #007bff;
            margin-right: 10px;
        }
        .logo .wayback {
            font-size: 3em;
            color: #343a40;
            font-weight: bold;
        }
        form {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid #007bff;
            border-radius: 8px;
            font-size: 16px;
            margin-right: 10px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            border-color: #0056b3;
            outline: none;
        }
        button {
            padding: 15px 25px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        button:hover {
            background-color: #0056b3;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        th {
            background-color: #f8f9fa;
            color: #495057;
            font-weight: 600;
        }
        tbody tr:hover {
            background-color: #e9ecef;
        }
        a {
            text-decoration: none;
            color: #007bff;
            font-weight: 600;
        }
        a:hover {
            text-decoration: underline;
        }
        .pagination {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        .pagination button {
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            margin: 0 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .pagination button:hover {
            background-color: #0056b3;
        }
        .pagination button[disabled] {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        .pagination .page-number {
            margin: 0 10px;
            font-size: 16px;
            line-height: 1.5;
            font-weight: 600;
        }
        .spinner {
            display: none;
            font-size: 24px;
            text-align: center;
            margin-top: 20px;
        }
        .spinner i {
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <div class="walrus">🦭</div>
            <div class="wayback">Walrus Wayback</div>
        </div>
        <form id="archiveForm">
            <input type="text" id="url" name="url" placeholder="https://example.com" required>
            <button type="submit">Archive</button>
        </form>
        <div id="spinner" class="spinner"><i class="fas fa-spinner fa-spin"></i> Archiving...</div>
        <h2>Recently Archived URLs</h2>
        <table id="archiveTable">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>URL</th>
                    <th>View</th>
                </tr>
            </thead>
            <tbody>
                $table_rows
            </tbody>
        </table>
        <div class="pagination">
            <button id="prevPage" onclick="changePage(-1)" $prev_disabled>Previous</button>
            <span class="page-number">Page $current_page of $total_pages</span>
            <button id="nextPage" onclick="changePage(1)" $next_disabled>Next</button>
        </div>
    </div>
    <script>
        document.getElementById('archiveForm').addEventListener('submit', async function(event) {
            event.preventDefault();
            document.getElementById('spinner').style.display = 'block';
            const url = document.getElementById('url').value;

            // Perform the archiving request using Fetch API
            const formData = new FormData();
            formData.append('url', url);
            
            try {
                const response = await fetch('/archive', {
                    method: 'POST',
                    body: formData
                });

                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    // Handle error if needed
                    alert('Archiving failed.');
                }
            } catch (error) {
                alert('An error occurred while archiving.');
            } finally {
                document.getElementById('spinner').style.display = 'none';
            }
        });

        function changePage(direction) {
            const newPage = $current_page + direction;
            window.location.href = `/?page=` + newPage;
        }
    </script>
                         <script>
    async function loadBlobAndOpen(filename) {
        try {
            const url = filename; // Assuming your server serves the file from this URL
            
            // Fetch the file as a blob
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error('Failed to fetch file:', response.status);
            }
            
            const blob = await response.blob();
            console.log(blob);
            const reader = new FileReader();

            reader.onload = function(event) {
                const htmlContent = event.target.result; // This contains the decoded HTML content
                // Open the HTML content in a new tab
                const newTab = window.open();
                newTab.document.write(htmlContent);
                newTab.document.close();
            };
            // Read the blob content as a text string (for HTML content)
            reader.readAsText(blob);
        } catch (error) {
            console.error('Error opening blob:', error);
        }
    }
</script>
</body>
</html>
""")

import re

def remove_parentheses_content(input_string):
    # Use regex to replace all content within parentheses including the parentheses
    return re.sub(r'\(.*?\)', '', input_string)

@app.get("/secret_old_path", response_class=HTMLResponse)
async def read_root(page: int = 1):
    # Read HTML files from the archive directory
    files = [f for f in os.listdir(BLOBS_DIR) ]
    #if f.endswith('.html')
    # Sort files by modification time
    files.sort(key=lambda x: os.path.getmtime(os.path.join(BLOBS_DIR, x)), reverse=True)
    
    # Pagination
    rows_per_page = 5
    start_index = (page - 1) * rows_per_page
    end_index = start_index + rows_per_page
    paginated_files = files[start_index:end_index]

    # Total pages calculation
    total_pages = (len(files) + rows_per_page - 1) // rows_per_page

    # Generate HTML table rows for recently archived URLs
    table_rows = ""
    for filename in paginated_files:
        if ".html" in filename: continue
        path = os.path.join(BLOBS_DIR, filename)
        timestamp = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        #url = filename.split("_", 1)[-1].replace("_", "/").replace(".html", "")
        with open(path, 'r') as file:
            real_name = file.read()
        url_display = remove_parentheses_content(real_name.replace("_", "/").replace(" ", ""))
        #url = urlunparse(('https', url, '', '', '', ''))  # Ensure HTTPS
        #url_display = urlparse(url).netloc  # Display only the domain
        domain = "https://aggregator-devnet.walrus.space/v1/"
        table_rows += f'<tr><td>{timestamp}</td><td>{url_display}</td><td><a onclick="loadBlobAndOpen(`{domain + filename}`); return false;">📄</a></td></tr>'

    prev_disabled = "disabled" if page == 1 else ""
    next_disabled = "disabled" if page == total_pages else ""

    # Render the HTML page
    return HTML_TEMPLATE.substitute(
        table_rows=table_rows, 
        current_page=page, 
        total_pages=total_pages, 
        prev_disabled=prev_disabled, 
        next_disabled=next_disabled
    )

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
