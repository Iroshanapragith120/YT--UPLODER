import os
import glob
import time
import re
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 🚀 අලුත් ලයිබ්‍රරි එක Import කරගන්නවා
from youtube_upload_no_api import YoutubeUpload

app = FastAPI()
VIDEO_DIR = "videos"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

class DownloadRequest(BaseModel):
    url: str
    custom_name: str

class UploadRequest(BaseModel):
    video_filename: str
    title: str
    description: str

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}

@app.post("/download")
async def download_video(req: DownloadRequest):
    safe_name = re.sub(r'[^\w\s\-\u0d80-\u0df4]', '', req.custom_name).strip()
    if not safe_name:
         safe_name = "downloaded_video_" + str(int(time.time()))
    
    filename = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
    url = req.url.strip()

    try:
        if not ("youtube.com" in url or "youtu.be" in url or "vimeo.com" in url):
            headers = {"User-Agent": "Mozilla/5.0"}
            with requests.get(url, headers=headers, stream=True, timeout=180) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return {"message": f"✅ සේව් සක්සස්! '{safe_name}.mp4' බාගත්තා!"}

        command = f'yt-dlp --no-check-certificates --no-playlist -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" "{url}" -o "{filename}"'
        exit_code = os.system(command)
        if exit_code != 0:
            os.system(f'yt-dlp --no-check-certificates --no-playlist -f "best" "{url}" -o "{filename}"')
            
        if not os.path.exists(filename):
            raise HTTPException(status_code=500, detail="බාගැනීම අසාර්ථක විය!")
        return {"message": f"✅ සේව් සක්සස්! '{safe_name}.mp4' බාගත්තා!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-videos")
def list_videos():
    files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    return {"videos": [os.path.basename(f) for f in files]}

# ========================================================
# 🔥 අලුත්ම NO-API / NO-SELENIUM UPLOAD FUNCTION එක
# ========================================================
@app.post("/upload")
async def upload_video(req: UploadRequest):
    full_path = os.path.abspath(os.path.join(VIDEO_DIR, req.video_filename))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="වීඩියෝව සර්වර් එකේ නැත!")

    # 🔑 ප්‍රොජෙක්ට් ෆෝල්ඩර් එක ඇතුළේ 'auth.txt' කියලා එකක් තියෙන්න ඕනේ (පියවර 3 බලන්න)
    auth_file = "auth.txt"
    if not os.path.exists(auth_file):
        raise HTTPException(status_code=500, detail="❌ 'auth.txt' ෆයිල් එක සර්වර් එකේ සොයාගත නොහැක!")

    try:
        print("🚀 Request ක්‍රමයට YouTube එකට වීඩියෝව තල්ලු කිරීම ආරම්භ කලා...")
        
        # ලයිබ්‍රරි එක Initialize කරනවා
        uploader = YoutubeUpload(auth_file=auth_file)
        
        # කෙලින්ම යූටියුබ් ඉන්ටර්නල් සර්වර් එකට වීඩියෝව තල්ලු කරනවා
        uploader.upload(
            file_path=full_path,
            title=req.title,
            description=req.description,
            privacy_status="public", # public, private, or unlisted
            made_for_kids=False
        )
        
        print("✅ අප්ලෝඩ් එක සාර්ථකයි!")
        
        # ඉඩ ඉතුරු කරගන්න සර්වර් එකේ තියෙන වීඩියෝව මකනවා
        if os.path.exists(full_path):
            os.remove(full_path)
            
        return {"message": "🔥 පට්ට මචන්! සෙලීනියම් ලෙඩ මොකුත් නැතුව, Direct Request එකක් විදිහට වීඩියෝව සාර්ථකව YouTube එකට තල්ලු වුණා!"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"තල්ලු කිරීම බිඳවැටුණා (Internal API Error): {str(e)}")
