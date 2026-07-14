import os
import requests
import asyncio
import traceback  # Error එක මොකක්ද කියලා සවිස්තරාත්මකව ගන්න
from fastapi import FastAPI, HTTPException, Form
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

# 🔑 auth.txt එක කියවීම
def get_auth_token():
    auth_file = "/content/YT--UPLODER/backend/auth.txt"
    if not os.path.exists(auth_file):
        raise HTTPException(status_code=500, detail="auth.txt file not found in backend folder!")
    with open(auth_file, "r") as f:
        return f.read().strip()

# =====================================================================
# 📥 1. DIRECT LINK DOWNLOAD API (Custom Name එකත් එක්ක)
# =====================================================================
@app.post("/download")
async def download_video(
    url: str = Form(...),
    custom_name: str = Form(None)  # Frontend එකෙන් එන Custom Name එක
):
    try:
        print(f"📥 වීඩියෝ එක බානවා: {url}")
        
        # නමක් දුන්නේ නැත්නම් auto name එකක් හදනවා
        if custom_name and custom_name.strip():
            # නමට අගින් .mp4 නැත්නම් ඒක එකතු කරනවා
            file_name = custom_name.strip()
            if not file_name.endswith(".mp4"):
                file_name += ".mp4"
        else:
            file_name = f"video_{int(asyncio.get_event_loop().time())}.mp4"
            
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        response = requests.get(url, stream=True, timeout=120)
        if response.status_code != 200:
            raise Exception("ලබාදුන් වීඩියෝ ලින්ක් එක වැඩ කරන්නේ නැත!")
            
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        print(f"✓ වීඩියෝ එක සාර්ථකව සේව් වුණා: {file_path}")
        return {
            "status": "success", 
            "message": f"'{file_name}' වීඩියෝව සාර්ථකව Cloud එකට බාගත්තා!", 
            "file_path": file_path,
            "file_name": file_name
        }
    except Exception as e:
        # Error එක Console එකෙත් පෙන්වනවා
        print(f"❌ බාගැනීමේ දෝෂය: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 📋 2. VIDEO LIST API
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
# 🚀 3. YOUTUBE UPLOAD API (සවිස්තරාත්මක Error Tracking සමඟ - FIXED)
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
            raise Exception(f"සර්වර් එකේ මේ වීඩියෝ එක නැත: {file_path}")

        # YouTube Upload Script එක ලෝඩ් කිරීම
        try:
            from youtube_upload_no_api import YoutubeUpload
        except ImportError as imp_err:
            raise Exception(f"youtube_upload_no_api.py ෆයිල් එක backend ෆෝල්ඩර් එකේ නැත! (Import Error: {str(imp_err)})")
        
        uploader = YoutubeUpload(auth_file="/content/YT--UPLODER/backend/auth.txt")
        
        # මෙතනදී Upload එක ඇතුළේ වෙන වැරදි වෙනම අල්ලගන්නවා
        try:
            success = uploader.upload(
                file_path=file_path,
                title=title,
                description=description,
                privacy_status="public"
            )
        except Exception as upload_inner_err:
            detailed_err = traceback.format_exc()
            raise Exception(f"Upload process එක ඇතුළත දෝෂයක්: {str(upload_inner_err)}\n\nTraceback:\n{detailed_err}")

        if success:
            if os.path.exists(file_path):
                os.remove(file_path)
            return {"status": "success", "message": f"'{title}' වීඩියෝව සාර්ථකව YouTube එකට අප්ලෝඩ් වුණා! 🎉"}
        else:
            raise Exception("YouTube Upload Script එක False ප්‍රතිචාරයක් ලබා දුන්නා. (Cookies/Auth ප්‍රශ්නයක් විය හැක)")
            
    except Exception as e:
        # සවිස්තරාත්මකව වැරැද්ද Console එකේ Print කරනවා
        error_details = traceback.format_exc()
        print(f"❌ YouTube Upload එක අසාර්ථක විය:\n{error_details}")
        
        # ⚠️ මෙන්න මෙතනයි බෙහෙත දැම්මේ: 
        # සර්වර් එක Crash නොවී, සරල Error පණිවිඩයක් ලෙස වැරැද්ද Frontend එකට යවනවා. 
        # එවිට පේජ් එක Refresh වෙන්නේ නැතිව, රතු කොටුවේ Error එක හැමදාටම රැඳේ!
        raise HTTPException(
            status_code=400, 
            detail=f"{str(e)}"
        )

# 🗂 4. FRONTEND STATIC FILE ROUTER
app.mount("/frontend", StaticFiles(directory="/content/YT--UPLODER/frontend"), name="frontend")

@app.get("/")
async def read_index():
    index_path = "/content/YT--UPLODER/frontend/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}
