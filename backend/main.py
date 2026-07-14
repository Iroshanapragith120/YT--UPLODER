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
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI()
VIDEO_DIR = "videos"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

# 💾 උඹ ලබාදුන් YouTube Cookies 12 කෙලින්ම කෝඩ් එකට ඇතුලත් කලා
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
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 💡 Cookies ඇතුල් කිරීමට ප්‍රථම YouTube වෙත යා යුතුය
        driver.get("https://www.youtube.com")
        time.sleep(3)
        
        print("කෝඩ් එකේ ඇති Cookies බ්‍රවුසර් එකට දමමින්...")
        for cookie in MY_YOUTUBE_COOKIES:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
                
        # 💡 දැන් කෙළින්ම YouTube Studio එකට (ලොගින් පිටු එන්නේ නැත)
        print("YouTube Studio වෙත පිවිසෙමින්...")
        driver.get("https://studio.youtube.com/channel/UC/videos?d=ud")
        time.sleep(7)
        
        print("වීඩියෝ ෆයිල් එක අප්ලෝඩ් කරමින්...")
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(full_path)
        time.sleep(8) 
        
        print("Title සහ Description සකසමින්...")
        title_box = driver.find_element(By.XPATH, "//div[@id='textbox' and @textbox-id='title-textbox']")
        title_box.clear()
        title_box.send_keys(req.title)
        
        desc_box = driver.find_element(By.XPATH, "//div[@id='textbox' and @textbox-id='description-textbox']")
        desc_box.clear()
        desc_box.send_keys(req.description)
        time.sleep(3)
        
        print("Next බටන් ක්ලික් කරමින්...")
        for _ in range(3):
            next_btn = driver.find_element(By.ID, "next-button")
            next_btn.click()
            time.sleep(4)
            
        print("වීඩියෝව Private ලෙස සකසමින්...")
        private_radio = driver.find_element(By.NAME, "PRIVATE")
        private_radio.click()
        time.sleep(3)
        
        print("අවසාන සේව් කිරීම සිදුකරමින්...")
        save_btn = driver.find_element(By.ID, "done-button")
        save_btn.click()
        time.sleep(8) 
        
        driver.quit()
        if os.path.exists(full_path):
            os.remove(full_path)
            
        return {"message": "🔥 ගේම සක්සස් මචන්! කිසිම බ්ලොක් එකක් නැතුව වීඩියෝව YouTube එකට ඔටෝ අප්ලෝඩ් වුණා!"}
        
    except Exception as e:
        driver.quit()
        raise HTTPException(status_code=500, detail=f"අප්ලෝඩ් වීම බිඳවැටුණා: {str(e)}")
