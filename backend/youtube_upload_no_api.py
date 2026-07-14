import os
import re
import json
import requests

class YoutubeUpload:
    def __init__(self, auth_file="auth.txt"):
        self.auth_file = auth_file
        self.session = requests.Session()
        self.load_cookies()

    def load_cookies(self):
        if not os.path.exists(self.auth_file):
            raise Exception(f"සමාවෙන්න, {self.auth_file} ෆයිල් එක සොයාගත නොහැක!")
            
        with open(self.auth_file, "r") as f:
            content = f.read().strip()

        try:
            cookie_data = json.loads(content)
            for cookie in cookie_data:
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.youtube.com'))
        except json.JSONDecodeError:
            lines = content.split('\n')
            for line in lines:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain, _, path, secure, _, name, value = parts[:7]
                    self.session.cookies.set(name, value, domain=domain, path=path)
                elif "=" in line:
                    name, value = line.split('=', 1)
                    self.session.cookies.set(name.strip(), value.strip(), domain=".youtube.com")
                else:
                    self.session.cookies.set("SAPISIDHASH", content, domain=".youtube.com")

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_innertube_key(self):
        response = self.session.get("https://youtube.com/upload")
        html = response.text
        
        api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
        client_version_match = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
        
        if not api_key_match:
            raise Exception("YouTube InnerTube API Key එක සොයාගත නොහැකි විය! කරුණාකර auth.txt එකේ Cookies වලංගු දැයි බලන්න. (Session Expired විය හැක)")
            
        return api_key_match.group(1), client_version_match.group(1) if client_version_match else "2.20240101.00.00"

    def upload(self, file_path, title, description, privacy_status="public"):
        if not os.path.exists(file_path):
            raise Exception(f"වීඩියෝ ෆයිල් එක නැත: {file_path}")

        api_key, client_version = self.get_innertube_key()
        
        upload_url = f"https://upload.youtube.com/upload/studio?authuser=0"
        file_size = os.path.getsize(file_path)
        
        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "X-Goog-Upload-Header-Content-Type": "video/mp4",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        }
        
        init_response = self.session.post(upload_url, headers=headers)
        if init_response.status_code != 200 or "X-Goog-Upload-URL" not in init_response.headers:
            raise Exception(f"YouTube Upload Server එක සමඟ සම්බන්ධ විය නොහැක! Status: {init_response.status_code}")
            
        chunk_upload_url = init_response.headers["X-Goog-Upload-URL"]
        
        with open(file_path, "rb") as f:
            upload_headers = {
                "X-Goog-Upload-Offset": "0",
                "X-Goog-Upload-Command": "upload, finalize",
                "Content-Type": "application/octet-stream"
            }
            upload_response = self.session.post(chunk_upload_url, headers=upload_headers, data=f)
            
        if upload_response.status_code != 200:
            raise Exception(f"වීඩියෝ දත්ත අප්ලෝඩ් කිරීම අසාර්ථක වුණා! Status: {upload_response.status_code}")
            
        scotty_resource_id = upload_response.json().get("scottyResourceId")
        if not scotty_resource_id:
            raise Exception("YouTube වෙතින් Scotty Resource ID එකක් ලැබුණේ නැත!")

        meta_url = f"https://studio.youtube.com/youtubei/v1/creator/create_video?key={api_key}"
        
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB_CREATOR",
                    "clientVersion": client_version
                }
            },
            "resourceId": {
                "scottyResourceId": scotty_resource_id
            },
            "frontendUploadId": f"ugc-upload-{os.path.basename(file_path)}",
            "title": title,
            "description": description,
            "privacy": privacy_status.upper()
        }
        
        meta_response = self.session.post(meta_url, json=payload)
        if meta_response.status_code == 200:
            return True
        else:
            raise Exception(f"Metadata update අසාර්ථකයි! Response: {meta_response.text}")
