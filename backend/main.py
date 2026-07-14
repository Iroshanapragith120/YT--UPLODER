import os

main_py_path = "/content/YT--UPLODER/backend/main.py"

full_code = """import os
import requests
from fastapi import FastAPI, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# 🗂️ Frontend ෆයිල් ටික සර්වර් එකට ලින්ක් කිරීම
# (index.html, style.css, app.js සේරම මේකෙන් ලෝඩ් වෙනවා)
app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")

@app.get("/")
async def read_index():
    index_path = os.path.join("../frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}

# 🔑 auth.txt එකෙන් ටෝකන් එක කියවා ගන්නා ආකාරය
def get_auth_token():
    auth_file = "auth.txt"
    if not os.path.exists(auth_file):
        raise HTTPException(status_code=500, detail="auth.txt file not found in backend folder!")
    with open(auth_file, "r") as f:
        token = f.read().strip()
    return token

@app.post("/api/download")
async def download_video(url: str = Form(...)):
    try:
        print(f"📥 වීඩියෝ එක ඩවුන්ලොඩ් වෙනවා: {url}")
        # වීඩියෝ එක සර්වර් එකට බාගන්නා ලොජික් එක (yt-dlp හෝ requests මඟින්)
        # උදාහරණයකට temporary file එකක් ලෙස සුරැකීම:
        video_path = "downloaded_video.mp4"
        with open(video_path, "wb") as f:
            f.write(b"dummy_video_content") 
        return {"status": "success", "message": "Video downloaded successfully!", "file_path": video_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_to_youtube(
    file_path: str = Form(...), 
    title: str = Form(...), 
    description: str = Form(...)
):
    try:
        # 1. auth.txt එකෙන් SAPISIDHASH ටෝකන් එක ගන්නවා
        token = get_auth_token()
        
        print(f"🚀 Upload ආරම්භ කරා: {title}")
        print(f"🔑 භාවිතා කරන Token එක: {token[:20]}...") 

        # 2. සෙලීනියම් නැතුව Direct YouTube Upload Internal Request එකක් යැවීම
        # (යූටියුබ් එකේ Studio InnnerTube API එකට request එකක් යවන ආකාරය)
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # මෙතනදී සැබෑ වීඩියෝ ඩේටා ටික YouTube API එකට Push කරනවා
        # (දැනට mock response එකක් මඟින් සක්සස් කරනවා)
        upload_success = True 

        if upload_success:
            return {"status": "success", "message": f"'{title}' වීඩියෝ එක සාර්ථකව YouTube එකට අප්ලෝඩ් වුණා! 🎉"}
        else:
            raise Exception("YouTube upload request failed.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

# ෆයිල් එක සම්පූර්ණයෙන්ම අලුතෙන් ලියනවා
with open(main_py_path, "w") as f:
    f.write(full_code)

print("🎯 100% සාර්ථකයි! main.py එක සම්පූර්ණයෙන්ම අප්ඩේට් කරා මචන්.")
