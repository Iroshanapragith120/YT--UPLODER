import os
import re
import json
import requests

class YoutubeUpload:
    def __init__(self, auth_file="auth.txt"):
        self.auth_file = auth_file
        self.session = requests.Session()
        self.cookies = {}
        self.load_cookies()

    def load_cookies(self):
        """
        auth.txt එකේ තියෙන Cookies හෝ SAPISIDHASH ටෝකන් එක කියවා 
        Requests Session එකට ඇතුළත් කිරීම.
        """
        if not os.path.exists(self.auth_file):
            raise Exception(f"සමාවෙන්න, {self.auth_file} ෆයිල් එක සොයාගත නොහැක!")
            
        with open(self.auth_file, "r") as f:
            content = f.read().strip()

        # මෙතනදී සරලවම auth.txt එකේ තියෙන්නේ Netscape Cookie Format එකක් හෝ JSON එකක් නම් ඒක ගලපා ගන්නවා
        try:
            # JSON format එකක් නම්
            cookie_data = json.loads(content)
            for cookie in cookie_data:
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.youtube.com'))
        except json.JSONDecodeError:
            # සරල ටෙක්ස්ට් එකක් (උදා: SAPISIDHASH විතරක්) හෝ Netscape format එකක් නම්
            lines = content.split('\n')
            for line in lines:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 7:
                    # Netscape format parser
                    domain, _, path, secure, _, name, value = parts[:7]
                    self.session.cookies.set(name, value, domain=domain, path=path)
                elif "=" in line:
                    # key=value format එකක් නම්
                    name, value = line.split('=', 1)
                    self.session.cookies.set(name.strip(), value.strip(), domain=".youtube.com")
                else:
                    # නිකන්ම SAPISIDHASH එක විතරක් තිබ්බොත්
                    self.session.cookies.set("SAPISIDHASH", content, domain=".youtube.com")

        # User-Agent එක Google Chrome එකකට සමාන කරනවා Google එකෙන් block නොකරන්න
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_innertube_key(self):
        """
        YouTube එකට Request යවන්න අවශ්‍ය InnerTube API Key එක සහ Client Data හොයාගැනීම.
        """
        response = self.session.get("https://youtube.com/upload")
        html = response.text
        
        # Innertube API Key එක regex මගින් සෙවීම
        api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
        client_version_match = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
        
        if not api_key_match:
            raise Exception("YouTube InnerTube API Key එක සොයාගත නොහැකි විය! කරුණාකර auth.txt එකේ Cookies වලංගු දැයි බලන්න.")
            
        return api_key_match.group(1), client_version_match.group(1) if client_version_match else "2.20240101.00.00"

    def upload(self, file_path, title, description, privacy_status="public"):
        """
        වීඩියෝ එක YouTube එකට Upload කරන ප්‍රධාන function එක.
        """
        try:
            if not os.path.exists(file_path):
                raise Exception(f"වීඩියෝ ෆයිල් එක නැත: {file_path}")

            print("🔑 YouTube Session එක සක්‍රීය කරමින්...")
            api_key, client_version = self.get_innertube_key()
            
            # 1. Upload URL එක ලබාගැනීම
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
                raise Exception("YouTube Upload Server එක සමඟ සම්බන්ධ විය නොහැක!")
                
            chunk_upload_url = init_response.headers["X-Goog-Upload-URL"]
            
            # 2. වීඩියෝ බයිට්ස් ටික අප්ලෝඩ් කිරීම (Chunk Upload)
            print(f"📤 වීඩියෝ දත්ත YouTube වෙත යවමින් පවතී ({round(file_size / (1024*1024), 2)} MB)...")
            with open(file_path, "rb") as f:
                upload_headers = {
                    "X-Goog-Upload-Offset": "0",
                    "X-Goog-Upload-Command": "upload, finalize",
                    "Content-Type": "application/octet-stream"
                }
                upload_response = self.session.post(chunk_upload_url, headers=upload_headers, data=f)
                
            if upload_response.status_code != 200:
                raise Exception("වීඩියෝ දත්ත අප්ලෝඩ් කිරීම අසාර්ථක වුණා!")
                
            # Response එකෙන් ලැබෙන Scoped Super Video ID එක ගැනීම
            scotty_resource_id = upload_response.json().get("scottyResourceId")
            if not scotty_resource_id:
                raise Exception("YouTube වෙතින් Video Resource ID එකක් ලැබුණේ නැත!")

            print("📝 වීඩියෝ විස්තර (Title, Description) ඇතුළත් කරමින්...")
            
            # 3. වීඩියෝවේ Metadata (Title, Desc, Privacy) සේව් කිරීම
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
                print("✓ සාර්ථකයි! වීඩියෝව YouTube වෙත එකතු කරන ලදී.")
                return True
            else:
                raise Exception(f"Metadata update අසාර්ථකයි: {meta_response.text}")

        except Exception as e:
            print(f"❌ වැරැද්දක් සිදුවුණා: {str(e)}")
            return False
