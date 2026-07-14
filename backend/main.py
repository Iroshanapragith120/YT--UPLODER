import os

main_py_path = "/content/YT--UPLODER/backend/main.py"

full_code = """import os
import requests
import asyncio
from fastapi import FastAPI, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🌐 CORS Setup (ලෙඩ නැතුව Frontend එකයි Backend එකයි කනෙක්ට් කරන්න)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📂 බාන වීඩියෝ තියාගන්න ෆෝල්ඩර් එක
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

# 📥 1. Video Download API (උඹේ Frontend එක ඉල්ලන නියම ලින්ක් එක: /download)
@app.post("/download")
async def download_video(url: str = Form(...)):
    try:
        print(f"📥 වීඩියෝ එක ඩවුන්ලොඩ් වෙනවා: {url}")
        
        file_name = f"video_{int(asyncio.get_event_loop().time())}.mp4"
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
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

# 📋 2. Video List API (උඹේ Frontend එක ඉල්ලන නියම ලින්ක් එක: /list-videos)
@app.get("/list-videos")
async def list_videos():
    try:
        if not os.path.exists(DOWNLOAD_DIR):
            return []
        files = os.listdir(DOWNLOAD_DIR)
        video_list = [{"name": f, "path": os.path.join(DOWNLOAD_DIR, f)} for f in files if f.endswith('.mp4')]
        return video_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 3. YouTube Upload API (උඹේ Frontend එක ඉල්ලන නියම ලින්ක් එක: /upload)
@app.post("/upload")
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

        # youtube_upload_no_api Script එක හරහා Upload කිරීම
        from youtube_upload_no_api import YoutubeUpload
        
        uploader = YoutubeUpload(auth_file="auth.txt")
        success = uploader.upload(
            file_path=file_path,
            title=title,
            description=description,
            privacy_status="public"
        )

        if success:
            if os.path.exists(file_path):
                os.remove(file_path)
            return {"status": "success", "message": f"'{title}' වීඩියോ එක සාර්ථකව YouTube එකට අප්ලෝඩ් වුණා! 🎉"}
        else:
            raise Exception("YouTube එකට තල්ලු කිරීම අසාර්ථක වුණා.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🗂 "frontend" ෆෝල්ඩර් එක Static Files විදිහට මවුන්ට් කිරීම
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

print("🎯 නියමයි මචන්! Frontend එකට හරියන විදිහට (404 Error නැතිවෙන්න) main.py එක සම්පූර්ණයෙන්ම හැදුවා.")
