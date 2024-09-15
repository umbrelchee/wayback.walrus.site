from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
import os
import subprocess

app = FastAPI()

ARCHIVE_DIR = "./archive"
os.makedirs(ARCHIVE_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
    <html>
        <head>
            <title>Wayback Machine</title>
        </head>
        <body>
            <h1>Simple Wayback Machine</h1>
            <form action="/archive" method="post">
                <label for="url">Enter URL to archive:</label>
                <input type="text" id="url" name="url">
                <button type="submit">Archive</button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/archive")
async def archive_page(url: str = Form(...)):
    try:
        # Run the ArchiveBox command to archive the given URL
        archivebox_command = f"archivebox add --depth=0 --extract '{url}'"
        subprocess.run(archivebox_command, shell=True, check=True)
        
        return {"message": "Page archived successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

