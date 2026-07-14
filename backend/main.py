import os
import glob
import time
import re
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

class DownloadRequest(BaseModel):
    url: str
    custom_name: str

class UploadRequest(BaseModel):
    video_filename: str
    title: str
    description: str
    email: str
    password: str

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
    # සිංහල, ඉංග්‍රීසි, ඉලක්කම් සපෝට් කරන ලෙස නම සුද්ධ කිරීම
    safe_name = re.sub(r'[^\w\s\-\u0d80-\u0df4]', '', req.custom_name).strip()
    if not safe_name:
         safe_name = "downloaded_video_" + str(int(time.time()))
    
    filename = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
    url = req.url.strip()

    try:
        # 💡 [ක්‍රමය 1] - ඩිරෙක්ට් ලින්ක් එකක්ද කියා පරික්ෂා කර කෙළින්ම බාගැනීම (Direct Download)
        # YouTube හෝ Vimeo නොවන වෙනත් ඕනෑම ඩිරෙක්ට් ලින්ක් එකක් නම්:
        if not ("youtube.com" in url or "youtu.be" in url or "vimeo.com" in url):
            print("Direct Link එකක් හඳුනාගන්නා ලදී! කෙළින්ම ක්ලවුඩ් එකට බාගැනීම ආරම්භ කරයි...")
            
            # Streaming මඟින් ලොකු ෆයිල් වුණත් සර්වර් එකේ Memory එක පිරෙන්නේ නැතිව බාගැනීම
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with requests.get(url, headers=headers, stream=True, timeout=180) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return {"message": f"✅ සේව් සක්සස්! (Direct Download) '{safe_name}.mp4' සාර්ථකව සේව් වුණා!"}

        # 💡 [ක්‍රමය 2] - YouTube ලින්ක් එකක් නම් පමණක් yt-dlp භාවිතයෙන් බාගැනීම
        print("YouTube ලින්ක් එකක් හඳුනාගන්නා ලදී! yt-dlp හරහා බාගැනීම ආරම්භ කරයි...")
        command = (
            f'yt-dlp --no-check-certificates --no-playlist '
            f'--user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" '
            f'-f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" '
            f'--merge-output-format mp4 "{url}" -o "{filename}"'
        )
        
        exit_code = os.system(command)
        
        # යම් හෙයකින් YouTube එකේ 1080p/Merge කේස් ආවොත් fallback එක දුවනවා
        if exit_code != 0 or not os.path.exists(filename):
            print("පළමු YouTube උත්සාහය අසාර්ථකයි! දෙවන (Fallback) ක්‍රමයෙන් උත්සාහ කරයි...")
            fallback_command = (
                f'yt-dlp --no-check-certificates --no-playlist '
                f'--user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" '
                f'-f "best" "{url}" -o "{filename}"'
            )
            os.system(fallback_command)
            
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            raise HTTPException(status_code=500, detail="බාගැනීම අසාර්ථක විය! ලින්ක් එක හෝ සර්වර් එක පරික්ෂා කරන්න.")
            
        return {"message": f"✅ සේව් සක්සස්! (YT Download) '{safe_name}.mp4' සාර්ථකව සේව් වුණා!"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"දෝෂයක් සිදුවිය: {str(e)}")

@app.get("/list-videos")
def list_videos():
    files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    video_list = [os.path.basename(f) for f in files]
    return {"videos": video_list}

@app.post("/upload")
async def upload_video(req: UploadRequest):
    full_path = os.path.abspath(os.path.join(VIDEO_DIR, req.video_filename))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="වීඩියෝ ෆයිල් එක සර්වර් එකේ නැත!")

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 1. Google Login
        driver.get("https://accounts.google.com/ServiceLogin?service=youtube")
        time.sleep(3)
        
        email_field = driver.find_element(By.NAME, "identifier")
        email_field.send_keys(req.email)
        driver.find_element(By.ID, "identifierNext").click()
        time.sleep(4)
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(req.password)
        driver.find_element(By.ID, "passwordNext").click()
        time.sleep(6)
        
        # 2. Go to YouTube Studio Upload
        driver.get("https://studio.youtube.com/channel/UC/videos?d=ud")
        time.sleep(5)
        
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(full_path)
        time.sleep(5) 
        
        title_box = driver.find_element(By.XPATH, "//div[@id='textbox' and @textbox-id='title-textbox']")
        title_box.clear()
        title_box.send_keys(req.title)
        
        desc_box = driver.find_element(By.XPATH, "//div[@id='textbox' and @textbox-id='description-textbox']")
        desc_box.clear()
        desc_box.send_keys(req.description)
        time.sleep(2)
        
        for _ in range(3):
            next_btn = driver.find_element(By.ID, "next-button")
            next_btn.click()
            time.sleep(3)
            
        private_radio = driver.find_element(By.NAME, "PRIVATE")
        private_radio.click()
        time.sleep(2)
        
        save_btn = driver.find_element(By.ID, "done-button")
        save_btn.click()
        time.sleep(5) 
        
        driver.quit()
        
        if os.path.exists(full_path):
            os.remove(full_path)
            
        return {"message": "🔥 සාර්ථකයි! Custom API එකෙන් වීඩියෝව ඔටෝම YouTube එකට දැම්මා, සර්වර් එකෙනුත් කැපුනා!"}
        
    except Exception as e:
        driver.quit()
        raise HTTPException(status_code=500, detail=f"ලොගින් වීම හෝ අප්ලෝඩ් වීම අසාර්ථකයි: {str(e)}")
