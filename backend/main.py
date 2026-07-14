import os
import traceback
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import HttpUrl

app = FastAPI()

# CORS සක්‍රීය කිරීම
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "downloads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/list-videos")
def list_videos():
    files = []
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            fp = os.path.join(UPLOAD_DIR, f)
            if os.path.isfile(fp):
                size_mb = os.path.getsize(fp) / (1024 * 1024)
                files.append({"name": f, "path": fp, "size": f"{size_mb:.2f} MB"})
    return files

@app.post("/download")
def download_video(url: str = Form(...), custom_name: str = Form(None)):
    try:
        import requests
        # නමක් දීලා නැත්නම් ලින්ක් එකෙන් නම ගන්නවා
        if not custom_name or not custom_name.strip():
            filename = url.split("/")[-1].split("?")[0]
            if not filename.endswith(".mp4"):
                filename += ".mp4"
        else:
            filename = custom_name.strip()
            if not filename.endswith(".mp4"):
                filename += ".mp4"
                
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Fast Download Process
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise Exception("ලින්ක් එකෙන් වීඩියෝව ලබාගත නොහැක!")
            
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        return {"status": "success", "message": f"වීඩියෝව සාර්ථකව බාගත්තා: {filename}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload")
def upload_to_youtube(file_path: str = Form(...), title: str = Form(...), description: str = Form(...)):
    # සර්වර් එක ක්‍රෑෂ් වෙන්න නොදී එරර් එක අල්ලගන්න Try/Except දැම්මා
    try:
        if not os.path.exists(file_path):
            raise Exception(f"සර්වර් එකේ මෙහෙම වීඩියෝ එකක් නැත: {file_path}")

        # --- මෙතනට උඹේ YouTube Upload Logic එක (youtube-upload ලයිබ්‍රරි එක) එනවා ---
        # උදාහරණයක් ලෙස: 
        # print(f"Uploading {file_path} with title: {title}")
        
        # ⚠️ පරීක්ෂා කිරීම සඳහා හිතාමතා Error එකක් මතු කරමු (ඇත්තටම වැඩ කරද්දී මේ raise කෑල්ල අයින් කරන්න)
        raise Exception("යූටියුබ් Cookies (auth.txt) Expired වී ඇත! කරුණාකර අලුත් Cookies දමන්න.")
        
        # සාර්ථක නම් වීඩියෝව මකා දැමීම (Auto Cleaner)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"status": "success", "message": "YouTube වෙත සාර්ථකව අප්ලෝඩ් කර Cloud එකෙන් මකා දැමුවා!"}

    except Exception as e:
        # මුළු සර්වර් එකම ක්‍රෑෂ් වෙන්න නොදී, වැරැද්ද විතරක් Frontend එකට යවනවා
        error_msg = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_msg)
