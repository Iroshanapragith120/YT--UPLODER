import os
import re
import json
import urllib.request
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
VIDEO_DIR = "downloaded_videos"
CONFIG_FILE = "config.json"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

class DownloadRequest(BaseModel):
    url: str
    custom_name: str

class UploadRequest(BaseModel):
    filename: str
    title: str
    description: str
    is_series: bool
    auth_code: str

def load_google_config():
    if not os.path.exists(CONFIG_FILE):
        raise HTTPException(status_code=500, detail="config.json ෆයිල් එක සර්වර් එකේ සොයාගත නොහැක!")
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config ෆයිල් එක කියවීමේ දෝෂයක්: {str(e)}")

# 📥 1. වීඩියෝ එක CUSTOM NAME එකෙන් බාන API එක
@app.post("/download")
def download_video(data: DownloadRequest):
    try:
        safe_name = data.custom_name.strip() if data.custom_name.strip() else "video"
        safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', safe_name)
        file_path = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
        
        req = urllib.request.Request(data.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
            out_file.write(response.read())
            
        return {"status": "success", "message": f"{safe_name}.mp4 නමින් වීඩියෝව සේව් වුණා!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🔑 2. YOUTUBE LOGIN ලින්ක් එක ගන්න API එක
@app.get("/get-auth-url")
def get_auth_url():
    client_config = load_google_config()
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    auth_url, _ = flow.authorization_url(prompt='consent')
    return {"auth_url": auth_url}

# 📤 3. YOUTUBE UPLOAD කරලා AUTO-DELETE (CUT) කරන API එක
@app.post("/upload")
def upload_and_cut_video(data: UploadRequest):
    file_path = os.path.join(VIDEO_DIR, data.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="වීඩියෝ ෆයිල් එක සර්වර් එකේ නැත!")
        
    try:
        client_config = load_google_config()
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        flow.fetch_token(code=data.auth_code)
        youtube = build('youtube', 'v3', credentials=flow.credentials)
        
        body = {
            'snippet': {'title': data.title, 'description': data.description, 'categoryId': '22'},
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
        }
        
        media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"status": "success", "video_id": response['id'], "message": "YouTube එකට අප්ලෝඩ් වුණා, සර්වර් එකෙන් මැකුණා!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🌐 🔥 💡 මෙන්න වැදගත්ම කොටස: FRONTEND එක සර්වර් එකට සම්බන්ධ කිරීම
# frontend ෆෝල්ඩර් එකේ තියෙන CSS, JS ෆයිල් ටික සර්වර් එකට ලෝඩ් කරනවා
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# ලින්ක් එකට ගියපු ගමන් index.html එක පෙන්වනවා
@app.get("/")
def read_index():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend files not found inside 'frontend' folder!"}
