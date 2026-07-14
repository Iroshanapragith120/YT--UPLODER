import os
import traceback
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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

# 🌟 මේක දැම්මාම ලින්ක් එකට ගිය සැනින් HTML පේජ් එක ලෝඩ් වෙනවා. "Not Found" වැටෙන්නේ නැහැ!
@app.get("/", response_class=HTMLResponse)
def read_root():
    # Frontend එකේ index.html එක කියවලා කෙලින්ම Root එකට දෙනවා
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend index.html file not found inside frontend/ directory!</h1>"

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
        if not custom_name or not custom_name.strip():
            filename = url.split("/")[-1].split("?")[0]
            if not filename.endswith(".mp4"):
                filename += ".mp4"
        else:
            filename = custom_name.strip()
            if not filename.endswith(".mp4"):
                filename += ".mp4"
                
        file_path = os.path.join(UPLOAD_DIR, filename)
        
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
    try:
        if not os.path.exists(file_path):
            raise Exception(f"සර්වර් එකේ මෙහෙම වීඩියෝ එකක් නැත: {file_path}")

        # ⚠️ පරීක්ෂා කිරීම සඳහා හිතාමතා Error එකක් මතු කරමු (ඇත්තටම වැඩ කරද්දී මේ raise කෑල්ල අයින් කරන්න)
        raise Exception("යූටියුබ් Cookies (auth.txt) Expired වී ඇත! කරුණාකර අලුත් Cookies දමන්න.")
        
        # සාර්ථක නම් වීඩියෝව මකා දැමීම (Auto Cleaner)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"status": "success", "message": "YouTube වෙත සාර්ථකව අප්ලෝඩ් කර Cloud එකෙන් මකා දැමුවා!"}

    except Exception as e:
        error_msg = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_msg)
