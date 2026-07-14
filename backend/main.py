import os
import glob
import time
import re
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI()
VIDEO_DIR = "videos"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

# 💾 YouTube Cookies 12
MY_YOUTUBE_COOKIES = [
    {"domain": ".youtube.com", "expirationDate": 1818587061.046194, "hostOnly": False, "httpOnly": True, "name": "__Secure-3PSID", "path": "/", "secure": True, "session": False, "storeId": None, "value": "g.a000_wjRxn3jNj8MdxiYXmwcvWU6m3KG6UhrnquU8KOEVrLK0bcpeoByj1mpgtfmzVp3KeO__wACgYKAf8SARESFQHGX2MiOUud5pfJYd5ZsMka147IthoVAUF8yKrjLsuAiRg6Q1bVMFACFB8Z0076"},
    {"domain": ".youtube.com", "expirationDate": 1815583072.349012, "hostOnly": False, "httpOnly": True, "name": "__Secure-1PSIDTS", "path": "/", "secure": True, "session": False, "storeId": None, "value": "sidts-CjQBPWEu2ZfRSAzxSjo81acwFSUQjQpck2vQaT33Ijj4yZHev2YGcGpYjFyVBK837cgTzWbPEAA"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.045709, "hostOnly": False, "httpOnly": False, "name": "SAPISID", "path": "/", "secure": True, "session": False, "storeId": None, "value": "tctucghL1B5qwdRe/Ao3mnLo3LCc6umTqO"},
    {"domain": ".youtube.com", "expirationDate": 1815583074.627283, "hostOnly": False, "httpOnly": True, "name": "__Secure-1PSIDCC", "path": "/", "secure": True, "session": False, "storeId": None, "value": "AKEyXzVZJNzYrNdTLdTXjwNP9_MFXO5Kf84cMWXQmzzsgK5iP6rw27rq8x_oC7SMin_zOfiCRj0"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.04562, "hostOnly": False, "httpOnly": True, "name": "SSID", "path": "/", "secure": True, "session": False, "storeId": None, "value": "AQ3bct0FU9WZ5Nrj1"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.045752, "hostOnly": False, "httpOnly": False, "name": "__Secure-1PAPISID", "path": "/", "secure": True, "session": False, "storeId": None, "value": "tctucghL1B5qwdRe/Ao3mnLo3LCc6umTqO"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.046152, "hostOnly": False, "httpOnly": True, "name": "__Secure-1PSID", "path": "/", "secure": True, "session": False, "storeId": None, "value": "g.a000_wjRxn3jNj8MdxiYXmwcvWU6m3KG6UhrnquU8KOEVrLK0bcpYOf2B5zltYnAzXz2tAEN1AACgYKAYkSARESFQHGX2Mik6A56lp4x9dP7NK89Z5czxoVAUF8yKobEoasyryJo35upyy1_vF-0076"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.045797, "hostOnly": False, "httpOnly": False, "name": "__Secure-3PAPISID", "path": "/", "secure": True, "session": False, "storeId": None, "value": "tctucghL1B5qwdRe/Ao3mnLo3LCc6umTqO"},
    {"domain": ".youtube.com", "expirationDate": 1815583074.627332, "hostOnly": False, "httpOnly": True, "name": "__Secure-3PSIDCC", "path": "/", "secure": True, "session": False, "storeId": None, "value": "AKEyXzWaMYgKjlOtoAnoPXSVyfCgRlWBoI8dBp0zumYESWl48CzR8AoXup22jo3el68dZ71aeLQ"},
    {"domain": ".youtube.com", "expirationDate": 1815583072.349112, "hostOnly": False, "httpOnly": True, "name": "__Secure-3PSIDTS", "path": "/", "secure": True, "session": False, "storeId": None, "value": "sidts-CjQBPWEu2ZfRSAzxSjo81acwFSUQjQpck2vQaT33Ijj4yZHev2YGcGpYjFyVBK837cgTzWbPEAA"},
    {"domain": ".youtube.com", "expirationDate": 1818587179.120868, "hostOnly": False, "httpOnly": True, "name": "LOGIN_INFO", "path": "/", "secure": True, "session": False, "storeId": None, "value": "AFmmF2swRQIgM56MBVkaXTrLkx-H5C19uiYVndh3XcMNVLZcTSbvQhkCIQCnV9f7S6-yI5G8D0LBHGQw2PuoM-C4ONcZAuD6WGgZAw:QUQ3MjNmeHE1Nnp5c0VSREJMZ184QVN6bDk5SUd6Z3ZNVEJOb21wLVZUMVY0eU9nd2xQYUt0MllFV0FneWdnbUlHdElNbXBMc0FGTmNlRml5N1BuYUZUaTJyQnAxNzh6eWdpSUt3SFpHeXR0M2NyNS1RYktnRGFPazlSc1VpUWM5ZzVrTTFCZm9yNkZyMGlkOWx5ZHBNbzZlM0pXZWREclBR"},
    {"domain": ".youtube.com", "expirationDate": 1818607070.152894, "hostOnly": False, "httpOnly": False, "name": "PREF", "path": "/", "secure": True, "session": False, "storeId": None, "value": "f6=40000000&tz=America.Montevideo"}
]

class DownloadRequest(BaseModel):
    url: str
    custom_name: str

class UploadRequest(BaseModel):
    video_filename: str
    title: str
    description: str

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing!"}

@app.post("/download")
async def download_video(req: DownloadRequest):
    safe_name = re.sub(r'[^\w\s\-\u0d80-\u0df4]', '', req.custom_name).strip()
    if not safe_name:
         safe_name = "downloaded_video_" + str(int(time.time()))
    
    filename = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
    url = req.url.strip()

    try:
        if not ("youtube.com" in url or "youtu.be" in url or "vimeo.com" in url):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with requests.get(url, headers=headers, stream=True, timeout=180) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return {"message": f"✅ සේව් සක්සස්! '{safe_name}.mp4' බාගත්තා!"}

        command = f'yt-dlp --no-check-certificates --no-playlist -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" "{url}" -o "{filename}"'
        exit_code = os.system(command)
        if exit_code != 0:
            os.system(f'yt-dlp --no-check-certificates --no-playlist -f "best" "{url}" -o "{filename}"')
            
        if not os.path.exists(filename):
            raise HTTPException(status_code=500, detail="බාගැනීම අසාර්ථක විය!")
        return {"message": f"✅ සේව් සක්සස්! '{safe_name}.mp4' බාගත්තා!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-videos")
def list_videos():
    files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    return {"videos": [os.path.basename(f) for f in files]}

@app.post("/upload")
async def upload_video(req: UploadRequest):
    full_path = os.path.abspath(os.path.join(VIDEO_DIR, req.video_filename))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="වීඩියෝව සර්වර් එකේ නැත!")

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080") # Full screen සෙට් කරනවා එලිමන්ට් නොහැංගෙන්න
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30) # උපරිම තත්පර 30ක් එලිමන්ට් එකක් එනකම් ඉවසන්න කියලා සෙට් කරනවා
    
    try:
        # 💡 මුලින්ම යූටියුබ් එකට යමු
        driver.get("https://www.youtube.com")
        time.sleep(5)
        
        print("Cookies ඇතුලත් කරමින්...")
        for cookie in MY_YOUTUBE_COOKIES:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
                
        # 💡 කෙළින්ම අප්ලෝඩ් ඩයලොග් එකට යමු
        print("YouTube Studio අප්ලෝඩ් පිටුවට පිවිසෙමින්...")
        driver.get("https://studio.youtube.com/channel/UC/videos?d=ud")
        time.sleep(10) # පිටුව සම්පූර්ණයෙන්ම ලෝඩ් වෙන්න ලොකු වෙලාවක් දෙනවා
        
        print("වීඩියෝ ෆයිල් එක සිලෙක්ට් කරමින්...")
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        file_input.send_keys(full_path)
        print("ෆයිල් එක සර්වර් එකට අප්ලෝඩ් වෙනකම් තත්පර 15ක් ඉවසනවා...")
        time.sleep(15) 
        
        # 🔥 මෙන්න මෙතන තමයි ක්‍රෑෂ් වුණේ. දැන් 'wait.until' දාලා තියෙන්නේ කොටුව පේනකම්ම ඉන්නවා.
        print("Title කොටුව සොයමින්...")
        title_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='textbox' and @textbox-id='title-textbox']")))
        title_box.clear()
        time.sleep(1)
        title_box.send_keys(req.title)
        print("Title එක ඇතුලත් කලා!")
        
        print("Description කොටුව සොයමින්...")
        desc_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='textbox' and @textbox-id='description-textbox']")))
        desc_box.clear()
        time.sleep(1)
        desc_box.send_keys(req.description)
        print("Description එක ඇතුලත් කලා!")
        time.sleep(3)
        
        print("Next බටන් 3 ක්ලික් කරමින් ඉදිරියට යමින්...")
        for i in range(3):
            next_btn = wait.until(EC.element_to_be_clickable((By.ID, "next-button")))
            next_btn.click()
            print(f"Next {i+1} ක්ලික් කලා")
            time.sleep(5)
            
        print("වීඩියෝව Private ලෙස සකසමින්...")
        private_radio = wait.until(EC.element_to_be_clickable((By.NAME, "PRIVATE")))
        private_radio.click()
        time.sleep(3)
        
        print("අවසාන සේව් බටන් එක ක්ලික් කරමින්...")
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "done-button")))
        save_btn.click()
        print("සම්පූර්ණයෙන්ම අප්ලෝඩ් වී අවසන් වනතුරු තත්පර 10ක් රැඳී සිටිනවා...")
        time.sleep(10) 
        
        driver.quit()
        if os.path.exists(full_path):
            os.remove(full_path)
            
        return {"message": "🔥 ගේම සක්සස් මචන්! කිසිම බ්ලොක් එකක් හෝ Error එකක් නැතුව වීඩියෝව YouTube එකට ඔටෝ අප්ලෝඩ් වුණා!"}
        
    except Exception as e:
        driver.quit()
        raise HTTPException(status_code=500, detail=f"අප්ලෝඩ් වීම බිඳවැටුණා: {str(e)}")
