import os
import glob
import time
import re
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
    # සිංහල අකුරු, ඉංග්‍රීසි අකුරු, ඉලක්කම් සහ space/hyphen/underscore හැමදේම සපෝට් කරන්න නම සුද්ධ කිරීම
    safe_name = re.sub(r'[^\w\s\-\u0d80-\u0df4]', '', req.custom_name).strip()
    if not safe_name:
         safe_name = "downloaded_video_" + str(int(time.time()))
    
    filename = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
    
    try:
        # පළමු උත්සාහය: උපරිම Quality එකෙන් (1080p/720p) වීඩියෝව සහ ඕඩියෝව වෙන වෙනම බාගෙන ffmpeg හරහා merge කිරීම.
        # බ්ලොක් නොවී බෑම සඳහා --no-check-certificates, --no-playlist සහ --user-agent එක් කර ඇත.
        command = (
            f'yt-dlp --no-check-certificates --no-playlist '
            f'--user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" '
            f'-f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" '
            f'--merge-output-format mp4 "{req.url}" -o "{filename}"'
        )
        
        print(f"Running command: {command}")
        exit_code = os.system(command)
        
        # යම් හෙයකින් පළමු ක්‍රමය අසාර්ථක වුණොත් හෝ ෆයිල් එක හැදුනේ නැත්නම්:
        if exit_code != 0 or not os.path.exists(filename):
            print("පළමු උත්සාහය අසාර්ථකයි! දෙවන (Fallback) ක්‍රමයෙන් උත්සාහ කරයි...")
            # දෙවන උත්සාහය: කෙලින්ම එකට Merge වෙලා තියෙන හොඳම format එක බෑම (මෙහිදී ffmpeg merge අවශ්‍ය නොවේ).
            fallback_command = (
                f'yt-dlp --no-check-certificates --no-playlist '
                f'--user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" '
                f'-f "best" "{req.url}" -o "{filename}"'
            )
            os.system(fallback_command)
            
        if not os.path.exists(filename):
            raise HTTPException(
                status_code=500, 
                detail="බාගැනීම අසාර්ථක විය! YouTube සීමාවක් නිසා හෝ ලින්ක් එකේ ගැටලුවක් විය හැක. නැවත උත්සාහ කරන්න."
            )
            
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
