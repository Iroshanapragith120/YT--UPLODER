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
from googleapiclient.http import MediaFileUpload

app = FastAPI()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# 💡 මතකය නැති නොවෙන්න ෆයිල් එකක සේව් කරන Helper Functions
VERIFIER_FILE = "verifier_state.txt"
LAST_VIDEO_FILE = "last_video_state.txt"

def save_state(filename, data):
    with open(filename, "w") as f:
        f.write(data)

def load_state(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read().strip()
    return ""

class DownloadRequest(BaseModel):
    url: str
    custom_name: str = "video"

class UploadRequest(BaseModel):
    filename: str
    title: str
    description: str
    is_series: bool = False
    auth_code: str

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}

def get_credentials_path():
    possible_names = ["config.json", "credentials.json", "client_secret.json"]
    for name in possible_names:
        if os.path.exists(name):
            return name
    for name in possible_names:
        parent_path = os.path.join("..", name)
        if os.path.exists(parent_path):
            return parent_path
    return None

# 🔑 1. YOUTUBE AUTH URL එක සෑදීම
@app.get("/get-auth-url")
def get_auth_url():
    json_path = get_credentials_path()
    if not json_path:
        raise HTTPException(status_code=500, detail="config.json ෆයිල් එක සොයාගත නොහැක!")
        
    try:
        flow = Flow.from_client_secrets_file(
            json_path,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/oauth2callback"
        )
        
        # 💡 මෙතනදී සාදන Code Verifier එක සදහටම මතක හිටින්න ෆයිල් එකක ලියනවා
        code_verifier = secrets.token_urlsafe(64)
        save_state(VERIFIER_FILE, code_verifier)
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
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

@app.get("/download-status-check")
def check():
    return {"status": "ready"}

# 📥 2. VIDEO DOWNLOAD
@app.post("/download")
async def download_video(req: DownloadRequest):
    safe_name = "".join([c for c in req.custom_name if c.isalpha() or c.isdigit() or c in ' _-']).strip()
    if not safe_name:
        safe_name = "video"
    filename = f"{safe_name}.mp4"
    
    try:
        print(f"Downloading video from: {req.url}")
        os.system(f'yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 "{req.url}" -o "{filename}"')
        
        if not os.path.exists(filename):
            raise HTTPException(status_code=500, detail="yt-dlp මඟින් වීඩියෝව බාගැනීමට අපොහොසත් විය!")
            
        # 💡 බාගත්ත වීඩියෝ එකේ නමත් ෆයිල් එකක සේව් කරලා තියාගන්නවා ආරක්ෂාවට
        save_state(LAST_VIDEO_FILE, filename)
        return {"message": f"වීඩියෝව සාර්ථකව සර්වර් එකට බාගත්තා! (නම: {filename})"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📤 3. YOUTUBE UPLOAD (ලෙඩ ඔක්කොම ෆික්ස් කරපු කොටස)
@app.post("/upload")
async def upload_video(req: UploadRequest):
    # 💡 ෆයිල් එකෙන් Code Verifier එක කියවා ගැනීම
    current_code_verifier = load_state(VERIFIER_FILE)
    if not current_code_verifier:
        raise HTTPException(status_code=400, detail="සර්වර් එකේ Code Verifier එක සොයාගත නොහැක! කරුණාකර නැවත 'Link YouTube Account' ලින්ක් එක ගන්න.")

    # 💡 සර්වර් එක රීෆ්‍රෙෂ් වුණත් ඇත්තම ෆයිල් නම මෙතනින් චෙක් කරනවා
    target_filename = req.filename
    if not os.path.exists(target_filename):
        backup_filename = load_state(LAST_VIDEO_FILE)
        if backup_filename and os.path.exists(backup_filename):
            target_filename = backup_filename
        else:
            raise HTTPException(status_code=404, detail=f"දෝෂයකි: ඩවුන්ලෝඩ් වුණු වීඩියෝ ෆයිල් එක ({target_filename}) සර්වර් එකේ සොයාගත නොහැක!")

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

        body = {
            'snippet': {
                'title': req.title,
                'description': req.description,
                'tags': ['auto_upload'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'private' 
            }
        }

        # ඇත්තම ඉලක්කගත ෆයිල් එක අප්ලෝඩ් කිරීම
        media = MediaFileUpload(target_filename, chunksize=1024*1024, resumable=True, mimetype='video/mp4')
        
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        print(f"Uploading {target_filename} chunks to YouTube...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        video_id = response.get("id", "UNKNOWN")
        youtube_link = f"https://youtu.be/{video_id}"
        
        # සාර්ථකව අප්ලෝඩ් වුණාම සර්වර් එකෙන් File එක මකා දැමීම
        if os.path.exists(target_filename):
            os.remove(target_filename)
            print(f"🗑️ සර්වර් එක පිරිසිදු කර {target_filename} මකා දමන ලදී.")
            
        # සේව් කරපු ස්ටේට් ෆයිල්ස් ටිකත් ක්ලීන් කරනවා
        if os.path.exists(VERIFIER_FILE): os.remove(VERIFIER_FILE)
        if os.path.exists(LAST_VIDEO_FILE): os.remove(LAST_VIDEO_FILE)

        return {
            "message": f"🔥 සාර්ථකයි! වීඩියෝව YouTube වෙත ගියා. සර්වර් එකෙන් සදහටම මැකී ගියා (Cut & Cleaned)!",
            "video_id": video_id,
            "youtube_url": youtube_link
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
