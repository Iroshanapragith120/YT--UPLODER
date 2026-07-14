import os
import requests
import asyncio
import traceback
from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "/content/YT--UPLODER/backend/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_auth_token():
    auth_file = "/content/YT--UPLODER/backend/auth.txt"
    if not os.path.exists(auth_file):
        return None
    with open(auth_file, "r") as f:
        return f.read().strip()

@app.post("/download")
async def download_video(url: str = Form(...), custom_name: str = Form(None)):
    try:
        file_name = custom_name.strip() if custom_name and custom_name.strip() else f"video_{int(asyncio.get_event_loop().time())}.mp4"
        if not file_name.endswith(".mp4"): file_name += ".mp4"
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        response = requests.get(url, stream=True, timeout=120)
        if response.status_code != 200:
            return {"status": "error", "detail": "ලින්ක් එක වැඩ කරන්නේ නැත!"}
            
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
                    
        return {"status": "success", "message": f"'{file_name}' සාර්ථකව බාගත්තා!", "file_path": file_path}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/upload")
async def upload_to_youtube(file_path: str = Form(...), title: str = Form(...), description: str = Form(...)):
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "detail": f"සර්වර් එකේ ෆයිල් එක නැත: {file_path}"}

        try:
            from youtube_upload_no_api import YoutubeUpload
        except ImportError:
            return {"status": "error", "detail": "youtube_upload_no_api.py ෆයිල් එක Backend ෆෝල්ඩරේ නැත!"}
        
        uploader = YoutubeUpload(auth_file="/content/YT--UPLODER/backend/auth.txt")
        
        try:
            success = uploader.upload(file_path=file_path, title=title, description=description, privacy_status="public")
        except Exception:
            return {"status": "error", "detail": traceback.format_exc()}

        if success:
            if os.path.exists(file_path): os.remove(file_path)
            return {"status": "success", "message": f"'{title}' සාර්ථකව අප්ලෝඩ් වුණා! 🎉"}
        return {"status": "error", "detail": "YouTube Upload Script එකෙන් දෝෂයක් ආවා (Cookies/Auth ප්‍රශ්නයක් විය හැක)."}
            
    except Exception:
        return {"status": "error", "detail": traceback.format_exc()}

app.mount("/frontend", StaticFiles(directory="/content/YT--UPLODER/frontend"), name="frontend")

@app.get("/")
async def read_index():
    return FileResponse("/content/YT--UPLODER/frontend/index.html")
