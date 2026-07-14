import os
import requests
import asyncio
from fastapi import FastAPI, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🌐 CORS Setup - Frontend එකයි Backend එකයි ලෙඩ නැතුව කනෙක්ට් කරන්න
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📂 බාන වීඩියෝ සේව් වෙන තැන (Colab storage එක ඇතුළේ backend/downloads)
DOWNLOAD_DIR = "/content/YT--UPLODER/backend/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 🔑 auth.txt එක කියවීම
def get_auth_token():
    auth_file = "/content/YT--UPLODER/backend/auth.txt"
    if not os.path.exists(auth_file):
        raise HTTPException(status_code=500, detail="auth.txt ෆයිල් එක backend ෆෝල්ඩර් එකේ නැත!")
    with open(auth_file, "r") as f:
        return f.read().strip()

# =====================================================================
# 📥 1. DIRECT LINK DOWNLOAD API (වීඩියෝ එක Cloud එකට බෑම)
# =====================================================================
@app.post("/download")
async def download_video(url: str = Form(...)):
    try:
        print(f"📥 වීඩියෝ එක Cloud එකට බානවා: {url}")
        
        # වීඩියෝ එකට නමක් දීම
        file_name = f"video_{int(asyncio.get_event_loop().time())}.mp4"
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        response = requests.get(url, stream=True, timeout=120)
        if response.status_code != 200:
            raise Exception("ලබාදුන් ලින්ක් එක වැඩ කරන්නේ නැත!")
            
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        print(f"✓ වීඩියෝ එක සාර්ථකව සේව් වුණා: {file_path}")
        return {
            "status": "success", 
            "message": "වීඩියෝ එක සාර්ථකව Cloud එකට බාගත්තා!", 
            "file_path": file_path,
            "file_name": file_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 📋 2. VIDEO LIST API (බාපු වීඩියෝ ලිස්ට් එක Frontend එකට යැවීම)
# =====================================================================
@app.get("/list-videos")
async def list_videos():
    try:
        if not os.path.exists(DOWNLOAD_DIR):
            return []
        files = os.listdir(DOWNLOAD_DIR)
        video_list = []
        for f in files:
            if f.endswith('.mp4'):
                full_path = os.path.join(DOWNLOAD_DIR, f)
                video_list.append({
                    "name": f, 
                    "path": full_path,
                    "size": f"{round(os.path.getsize(full_path) / (1024*1024), 2)} MB"
                })
        return video_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 🚀 3. YOUTUBE UPLOAD API (තෝරාගත් වීඩියෝව YT එකට තල්ලු කිරීම)
# =====================================================================
@app.post("/upload")
async def upload_to_youtube(
    file_path: str = Form(...), 
    title: str = Form(...), 
    description: str = Form(...)
):
    try:
        token = get_auth_token()
        print(f"🚀 YouTube Upload ආරම්භ කළා: {title} | File: {file_path}")
        
        if not os.path.exists(file_path):
            raise Exception("අදාළ වීඩියෝ ෆයිල් එක සර්වර් එකේ සොයාගත නොහැක!")

        # අපේ No-API uploader script එක ලෝඩ් කිරීම
        from youtube_upload_no_api import YoutubeUpload
        
        uploader = YoutubeUpload(auth_file="/content/YT--UPLODER/backend/auth.txt")
        success = uploader.upload(
            file_path=file_path,
            title=title,
            description=description,
            privacy_status="public"
        )

        if success:
            # අප්ලෝඩ් වුණාට පස්සේ ඉඩ ඉතුරු කරගන්න සර්වර් එකෙන් වීඩියෝව මකනවා
            if os.path.exists(file_path):
                os.remove(file_path)
            return {"status": "success", "message": f"'{title}' වීඩියෝව සාර්ථකව YouTube එකට අප්ලෝඩ් වුණා! 🎉"}
        else:
            raise Exception("YouTube එකට අප්ලෝඩ් කිරීම අසාර්ථක වුණා.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🗂 4. FRONTEND STATIC FILE ROUTER
app.mount("/frontend", StaticFiles(directory="/content/YT--UPLODER/frontend"), name="frontend")

@app.get("/")
async def read_index():
    index_path = "/content/YT--UPLODER/frontend/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}
