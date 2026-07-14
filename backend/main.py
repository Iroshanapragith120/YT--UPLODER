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

# 💾 උඹ එවපු අලුත්ම YouTube Cookies ටික මෙතනට අප්ඩේට් කලා මචන්
MY_YOUTUBE_COOKIES = [
    {"domain": ".youtube.com", "expirationDate": 1818587061.046194, "hostOnly": False, "httpOnly": True, "name": "__Secure-3PSID", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": None, "value": "g.a000_wjRxn3jNj8MdxiYXmwcvWU6m3KG6UhrnquU8KOEVrLK0bcpeoByj1mpgtfmzVp3KeO__wACgYKAf8SARESFQHGX2MiOUud5pfJYd5ZsMka147IthoVAUF8yKrjLsuAiRg6Q1bVMFACFB8Z0076"},
    {"domain": ".youtube.com", "expirationDate": 1815584278.283069, "hostOnly": False, "httpOnly": True, "name": "__Secure-1PSIDTS", "path": "/", "sameSite": "Lax", "secure": True, "session": False, "storeId": None, "value": "sidts-CjQBPWEu2clVNkrv7yKiYridQkEZXgTRn8Z6MJaFaJGteZXW85zKh0qAJjkOY1KV2-j6FLNvEAA"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.045709, "hostOnly": False, "httpOnly": False, "name": "SAPISID", "path": "/", "sameSite": "Lax", "secure": True, "session": False, "storeId": None, "value": "tctucghL1B5qwdRe/Ao3mnLo3LCc6umTqO"},
    {"domain": ".youtube.com", "expirationDate": 1815584472.371569, "hostOnly": False, "httpOnly": True, "name": "__Secure-1PSIDCC", "path": "/", "sameSite": "Lax", "secure": True, "session": False, "storeId": None, "value": "AKEyXzWZxn6Q6nudDj2ObPwPsQS1JDyY8PeY5GSMxRl5d5LmoVJg9IY7-Bh8jXBGh9wIiGyXagE"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.04562, "hostOnly": False, "httpOnly": True, "name": "SSID", "path": "/", "sameSite": "Lax", "secure": True, "session": False, "storeId": None, "value": "AQ3bct0FU9WZ5Nrj1"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.045752, "hostOnly": False, "httpOnly": False, "name": "__Secure-1PAPISID", "path": "/", "sameSite": "Lax", "secure": True, "session": False, "storeId": None, "value": "tctucghL1B5qwdRe/Ao3mnLo3LCc6umTqO"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.046152, "hostOnly": False, "httpOnly": True, "name": "__Secure-1PSID", "path": "/", "sameSite": "Lax", "secure": True, "session": False, "storeId": None, "value": "g.a000_wjRxn3jNj8MdxiYXmwcvWU6m3KG6UhrnquU8KOEVrLK0bcpYOf2B5zltYnAzXz2tAEN1AACgYKAYkSARESFQHGX2Mik6A56lp4x9dP7NK89Z5czxoVAUF8yKobEoasyryJo35upyy1_vF-0076"},
    {"domain": ".youtube.com", "expirationDate": 1818587061.045797, "hostOnly": False, "httpOnly": False, "name": "__Secure-3PAPISID", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": None, "value": "tctucghL1B5qwdRe/Ao3mnLo3LCc6umTqO"},
    {"domain": ".youtube.com", "expirationDate": 1815584472.371618, "hostOnly": False, "httpOnly": True, "name": "__Secure-3PSIDCC", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": None, "value": "AKEyXzVUWMtyU0m-Fb3dQtF3AtepbWo_-oW9x-awCRjkhpRoT_4yuy0Em8nJjMVshUBeFdrleOA"},
    {"domain": ".youtube.com", "expirationDate": 1815584278.28317, "hostOnly": False, "httpOnly": True, "name": "__Secure-3PSIDTS", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": None, "value": "sidts-CjQBPWEu2clVNkrv7yKiYridQkEZXgTRn8Z6MJaFaJGteZXW85zKh0qAJjkOY1KV2-j6FLNvEAA"},
    {"domain": ".youtube.com", "expirationDate": 1818587179.120868, "hostOnly": False, "httpOnly": True, "name": "LOGIN_INFO", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": None, "value": "AFmmF2swRQIgM56MBVkaXTrLkx-H5C19uiYVndh3XcMNVLZcTSbvQhkCIQCnV9f7S6-yI5G8D0LBHGQw2PuoM-C4ONcZAuD6WGgZAw:QUQ3MjNmeHE1Nnp5c0VSREJMZ184QVN6bDk5SUd6Z3ZNVEJOb21wLVZUMVY0eU9nd2xQYUt0MllFV0FneWdnbUlHdElNbXBMc0FGTmNlRml5N1BuYUZUaTJyQnAxNzh6eWdpSUt3SFpHeXR0M2NyNS1RYktnRGFPazlSc1VpUWM5ZzVrTTFCZm9yNkZyMGlkOWx5ZHBNbzZlM0pXZWREclBR"},
    {"domain": ".youtube.com", "expirationDate": 1818608462.851266, "hostOnly": False, "httpOnly": False, "name": "PREF", "path": "/", "sameSite": "Lax", "secure": True, "session": False, "storeId": None, "value": "f6=40000000&tz=America.Montevideo"}
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
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 35) # පොඩ්ඩක් ඉවසන වෙලාව වැඩි කලා මචන්
    
    try:
        driver.get("https://studio.youtube.com")
        time.sleep(3)
        
        for cookie in MY_YOUTUBE_COOKIES:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
                
        driver.get("https://studio.youtube.com")
        time.sleep(8)
        
        # 🛡️ [ආරක්ෂක වැටක් දැම්මා]: Cookies වැඩ නැතුව Google Login පිටුවට ගියොත් මෙතනින් නවතිනවා
        if "accounts.google.com" in driver.current_url:
            raise HTTPException(status_code=401, detail="❌ Cookies Expired! (දීපු කුකීස් ටික යූටියුබ් එකෙන් ප්‍රතික්ෂේප කලා. ආයෙත් අලුත් කුකීස් ටිකක් දාන්න වෙයි).")
        
        # 👆 Upload බටන් එක එනකම් ඉඳලා ක්ලික් කරනවා
        upload_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//ytcp-button[@id="upload-button"]')))
        upload_btn.click()
        time.sleep(2)
        
        # 📁 File Input එකට වීඩියෝ එකේ Path එක දෙනවා
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        file_input.send_keys(full_path)
        time.sleep(8) 
        
        # ✍️ Title එක දානවා (අලුත්ම නිවැරදි XPath එක)
        title_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="textbox" and @aria-label="Add a title that describes your video (required)"]')))
        title_box.clear()
        time.sleep(1)
        title_box.send_keys(req.title)
        
        # ✍️ Description එක දානවා
        desc_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="textbox" and @aria-label="Tell viewers about your video"]')))
        desc_box.clear()
        time.sleep(1)
        desc_box.send_keys(req.description)
        
        # 👶 'Not Made for Kids' අනිවාර්යයෙන්ම සිලෙක්ට් කරනවා (නැත්නම් Next යන්න බෑ)
        kids_radio = wait.until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-radio-button[@name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')))
        kids_radio.click()
        time.sleep(2)
        
        # ➡️ Next බටන් 3 පාරක් ඔබනවා
        for i in range(3):
            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//ytcp-button[@id="next-button"]')))
            next_btn.click()
            time.sleep(3)
            
        # 🌍 වීඩියෝ එක Public කරනවා
        public_radio = wait.until(EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-radio-button[@name="PUBLIC"]')))
        public_radio.click()
        time.sleep(2)
        
        # 🚀 අවසාන වශයෙන් Done/Publish බටන් එක ක්ලික් කරනවා
        done_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//ytcp-button[@id="done-button"]')))
        done_btn.click()
        time.sleep(10) 
        
        driver.quit()
        if os.path.exists(full_path):
            os.remove(full_path)
            
        return {"message": "🔥 ගේම සක්සස් මචන්! අලුත්ම Cookies එක්ක කිසිම බ්ලොක් එකක් නැතුව වීඩියෝව YouTube එකට ඔටෝ අප්ලෝඩ් වුණා!"}
        
    except HTTPException as he:
        driver.quit()
        raise he
    except Exception as e:
        driver.quit()
        raise HTTPException(status_code=500, detail=f"අප්ලෝඩ් වීම බිඳවැටුණා: {str(e)}")
