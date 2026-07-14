import os
import re
import urllib.request
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI()

# Frontend එකයි Backend එකයි එකතු කරන්න (CORS Settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
VIDEO_DIR = "downloaded_videos"

# වීඩියෝ සේව් වෙන්න ෆෝල්ඩර් එකක් හදනවා
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

# 📥 1. වීඩියෝ එක CUSTOM NAME එකෙන් බාන API එක
@app.post("/download")
def download_video(data: DownloadRequest):
    try:
        # පරිශීලකයා නමක් දුන්නේ නැත්නම් default නමක් දානවා
        safe_name = data.custom_name.strip() if data.custom_name.strip() else "video"
        # නමේ වෙනත් කැත අකුරු (Symbols) තියෙනවා නම් අයින් කරනවා
        safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', safe_name)
        
        file_path = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
        
        # වීඩියෝ එක ඩවුන්ලෝඩ් කරනවා
        req = urllib.request.Request(data.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
            out_file.write(response.read())
            
        return {"status": "success", "message": f"සැලකූ නම වන {safe_name}.mp4 නමින් වීඩියෝව සේව් වුණා!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🔑 2. YOUTUBE LOGIN ලින්ක් එක ගන්න API එක
@app.get("/get-auth-url")
def get_auth_url():
    if not os.path.exists('client_secret.json'):
        raise HTTPException(status_code=400, detail="client_secret.json ෆයිල් එක නැත!")
    
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', scopes=SCOPES)
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
        # Authenticate කිරීම
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            'client_secret.json', scopes=SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        flow.fetch_token(code=data.auth_code)
        youtube = build('youtube', 'v3', credentials=flow.credentials)
        
        # YouTube එකට යන විස්තර ටික සෙට් කිරීම
        body = {
            'snippet': {
                'title': data.title,
                'description': data.description,
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        # වීඩියෝව අප්ලෝඩ් කිරීම
        media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            
        # 🔥 💡 උඹ ඉල්ලපු වැදගත්ම දේ: UPLOAD වුණු ගමන් සර්වර් එකෙන් ඩිලීට් කිරීම!
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ සර්වර් එක පිරිසිදු කරමින්: {data.filename} සාර්ථකව මැකුවා!")
            
        return {"status": "success", "video_id": response['id'], "message": "YouTube එකට අප්ලෝඩ් වුණා, සර්වර් එකෙන් මැකුණා!"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
