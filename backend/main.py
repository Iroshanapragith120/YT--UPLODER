import os

main_py_path = "/content/YT--UPLODER/backend/main.py"

full_code = """import os
import requests
import asyncio
from fastapi import FastAPI, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 🌐 CORS Setup (Frontend එකයි Backend එකයි ලෙඩ නැතුව කතා කරගන්න)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📂 බාන වීඩියෝ තියාගන්න ෆෝල්ඩර් එකක් හදනවා
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 🔑 auth.txt එකෙන් SAPISIDHASH ටෝකන් එක කියවීම
def get_auth_token():
    auth_file = "auth.txt"
    if not os.path.exists(auth_file):
        raise HTTPException(status_code=500, detail="auth.txt file not found in backend folder!")
    with open(auth_file, "r") as f:
        token = f.read().strip()
    return token

# 📥 1. Video Download API (Direct URL එකෙන් සර්වර් එකට බානවා)
@app.post("/api/download")
async def download_video(url: str = Form(...)):
    try:
        print(f"📥 වීඩියෝ එක ඩවුන්ලොඩ් වෙනවා: {url}")
        
        # ෆයිල් එක සේව් කරන නම
        file_name = f"video_{int(asyncio.get_event_loop().time())}.mp4"
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        # සෘජුවම ලින්ක් එකෙන් වීඩියෝ එක බාගැනීම
        response = requests.get(url, stream=True, timeout=60)
        if response.status_code != 200:
            raise Exception("වීඩියෝ ලින්ක් එක වැඩ කරන්නේ නැත!")
            
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        return {
            "status": "success", 
            "message": "වීඩියෝ එක සාර්ථකව බාගත්තා!", 
            "file_path": file_path,
            "file_name": file_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📋 2. Video List API (Frontend එක ලැයිස්තුව ඉල්ලන කොටුව)
@app.get("/api/videos")
async def list_videos():
    try:
        if not os.path.exists(DOWNLOAD_DIR):
            return []
        files = os.listdir(DOWNLOAD_DIR)
        video_list = [{"name": f, "path": os.path.join(DOWNLOAD_DIR, f)} for f in files if f.endswith('.mp4')]
        return video_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 3. YouTube Upload API (සෙලීනියම් නැති Direct Request ක්‍රමය)
@app.post("/api/upload")
async def upload_to_youtube(
    file_path: str = Form(...), 
    title: str = Form(...), 
    description: str = Form(...)
):
    try:
        token = get_auth_token()
        print(f"🚀 Upload ආරම්භ කරා: {title}")
        
        if not os.path.exists(file_path):
            raise Exception("අදාළ වීඩියෝ ෆයිල් එක සර්වර් එකේ නැත!")

        # 🚨 මෙතනදී තමයි අපේ අලුත් youtube_upload_no_api Script එක වැඩ කරන්නේ
        from youtube_upload_no_api import YoutubeUpload
        
        # අපි සාදාගත් අලුත් module එකෙන් upload එක සිදු කිරීම
        uploader = YoutubeUpload(auth_file="auth.txt")
        success = uploader.upload(
            file_path=file_path,
            title=title,
            description=description,
            privacy_status="public"
        )

        if success:
            # අප්ලෝඩ් වුණාට පස්සේ සර්වර් එකේ ඉඩ ඉතුරු කරන්න බාපු ෆයිල් එක මකනවා
            if os.path.exists(file_path):
                os.remove(file_path)
            return {"status": "success", "message": f"'{title}' වීඩියෝ එක සාර්ථකව YouTube එකට අප්ලෝඩ් වුණා! 🎉"}
        else:
            raise Exception("YouTube එකට තල්ලු කිරීම අසාර්ථක වුණා.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🗂️ 4. Frontend Router (HTML/CSS/JS සර්ව් කිරීම)
app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")

@app.get("/")
async def read_index():
    index_path = os.path.join("../frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}
"""

with open(main_py_path, "w") as f:
    f.write(full_code)

print("🎯 main.py එක 100% ක්ම නිවැරදිව සහ සියලුම API Routes සමඟ අප්ඩේට් කරා මචන්!")
