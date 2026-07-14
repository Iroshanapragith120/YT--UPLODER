import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload

app = FastAPI()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
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
    for name in ["config.json", "credentials.json", "client_secret.json"]:
        if os.path.exists(name): return name
        parent = os.path.join("..", name)
        if os.path.exists(parent): return parent
    return None

@app.get("/get-auth-url")
def get_auth_url():
    json_path = get_credentials_path()
    if not json_path:
        raise HTTPException(status_code=500, detail="config.json ෆයිල් එක සොයාගත නොහැක!")
    try:
        # Colab එකේ වැඩ කරන්න localhost redirect URI එක භාවිතා කරයි
        flow = Flow.from_client_secrets_file(
            json_path,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/oauth2callback"
        )
        auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download")
async def download_video(req: DownloadRequest):
    safe_name = "".join([c for c in req.custom_name if c.isalpha() or c.isdigit() or c in ' _-']).strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="වලංගු නමක් දෙන්න!")
    
    filename = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
    
    try:
        # yt-dlp මඟින් වීඩියෝව බාගැනීම
        os.system(f'yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 "{req.url}" -o "{filename}"')
        
        if not os.path.exists(filename):
            raise HTTPException(status_code=500, detail="බාගැනීම අසාර්ථක විය! ලින්ක් එක පරීක්ෂා කරන්න.")
        return {"message": f"✅ සේව් සක්සස්! '{safe_name}.mp4' සාර්ථකව සේව් වුණා!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-videos")
def list_videos():
    files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    video_list = [os.path.basename(f) for f in files]
    return {"videos": video_list}

@app.post("/upload")
async def upload_video(req: UploadRequest):
    full_path = os.path.join(VIDEO_DIR, req.video_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="වීඩියෝ ෆයිල් එක සර්වර් එකේ නැත!")

    json_path = get_credentials_path()
    try:
        flow = Flow.from_client_secrets_file(json_path, scopes=SCOPES, redirect_uri="http://localhost:8000/oauth2callback")
        flow.fetch_token(code=req.auth_code)
        credentials = flow.credentials

        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        body = {
            'snippet': {
                'title': req.title,
                'description': req.description,
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'private'
            }
        }

        media = MediaFileUpload(full_path, chunksize=1024*1024, resumable=True, mimetype='video/mp4')
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()

        # ✂️ සාර්ථකව අප්ලෝඩ් වූ පසු සර්වර් එකෙන් මකා දැමීම
        if os.path.exists(full_path):
            os.remove(full_path)

        video_id = response.get("id", "UNKNOWN")
        return {
            "message": f"🔥 සාර්ථකයි! වීඩියෝව YouTube වෙත ගියා, සර්වර් එකෙන් කැපුනා!",
            "youtube_url": f"https://youtu.be/{video_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
