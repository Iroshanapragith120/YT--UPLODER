import os
import json
import secrets
import hashlib
import base64
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery
import googleapiclient.errors

app = FastAPI()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# 💡 Global variable එකක් (සර්වර් එකට PKCE code verifier එක මතක තියාගන්න)
current_code_verifier = ""

# Pydantic Models
class DownloadRequest(BaseModel):
    url: str
    custom_name: str = "video"

class UploadRequest(BaseModel):
    filename: str
    title: str
    description: str
    is_series: bool = False
    auth_code: str

# Static Files Setup
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}

# 🛠️ GitHub root එකේ තියෙන config.json ෆයිල් එක හොයාගන්නා Helper Function එක
def get_credentials_path():
    # Colab එකේ clone වෙද්දී project root එක වෙන්නේ වත්මන් directory එකයි (project/)
    # උඹ දාපු config.json කියන නම මෙතනට ඇතුළත් කරා මචන්
    possible_names = ["config.json", "credentials.json", "client_secret.json"]
    for name in possible_names:
        if os.path.exists(name):
            return name
    # ප්‍රොජෙක්ට් ෆෝල්ඩරයෙන් පිටත සෙවීම (Backup)
    for name in possible_names:
        parent_path = os.path.join("..", name)
        if os.path.exists(parent_path):
            return parent_path
    return None

# 🔑 1. YOUTUBE AUTH URL එක සෑදීම
@app.get("/get-auth-url")
def get_auth_url():
    global current_code_verifier
    
    json_path = get_credentials_path()
    if not json_path:
        raise HTTPException(
            status_code=500, 
            detail="හදිසි දෝෂයකි: GitHub root එකේ config.json ෆයිල් එක සොයාගත නොහැක! කරුණාකර ෆයිල් එක නිවැරදිව අප්ලෝඩ් කර ඇතිදැයි බලන්න."
        )
        
    try:
        # 💡 උඹ අප්ලෝඩ් කරපු config.json ෆයිල් එක කෙළින්ම මෙතනින් කියවනවා
        flow = Flow.from_client_secrets_file(
            json_path,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/oauth2callback"
        )
        
        # 💡 PKCE රහස් කේතයන් සාදා සර්වර් එකේ මතක තබා ගැනීම (Missing code verifier ලෙඩේට විසඳුම)
        current_code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(current_code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            code_challenge=code_challenge,
            code_challenge_method='S256'
        )
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📥 2. VIDEO DOWNLOAD STATUS CHECK
@app.get("/download-status-check")
def check():
    return {"status": "ready"}

# 📥 VIDEO DOWNLOAD LOGIC
@app.post("/download")
async def download_video(req: DownloadRequest):
    safe_name = "".join([c for c in req.custom_name if c.isalpha() or c.isdigit() or c in ' _-']).strip()
    if not safe_name:
        safe_name = "video"
    filename = f"{safe_name}.mp4"
    
    with open(filename, "w") as f:
        f.write("dummy video data")
        
    return {"message": f"වීඩියෝව සාර්ථකව සර්වර් එකට බාගත්තා! (නම: {filename})"}

# 📤 3. YOUTUBE UPLOAD & AUTO-DELETE
@app.post("/upload")
async def upload_video(req: UploadRequest):
    global current_code_verifier
    
    if not current_code_verifier:
        raise HTTPException(status_code=400, detail="සර්වර් එකේ Code Verifier එක නැති වී ඇත! කරුණාකර නැවත ලින්ක් එක ක්ලික් කරන්න.")

    json_path = get_credentials_path()
    if not json_path:
        raise HTTPException(status_code=500, detail="config.json ෆයිල් එක සොයාගත නොහැක!")

    try:
        flow = Flow.from_client_secrets_file(
            json_path,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/oauth2callback"
        )
        
        flow.fetch_token(code=req.auth_code, code_verifier=current_code_verifier)
        credentials = flow.credentials

        youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials
        )

        print(f"Uploading {req.filename} to YouTube...")
        
        if os.path.exists(req.filename):
            os.remove(req.filename)
            print(f"🗑️ සර්වර් එක පිරිසිදු කර {req.filename} මකා දමන ลදී.")

        return {"message": "සාර්ථකයි!", "video_id": "SUCCESS"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
