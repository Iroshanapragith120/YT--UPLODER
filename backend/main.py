import os
import glob
import time
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
    safe_name = "".join([c for c in req.custom_name if c.isalpha() or c.isdigit() or c in ' _-']).strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="වලංගු නමක් දෙන්න!")
    
    filename = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
    try:
        # Colab එකේ ඩේටා වලින්ම yt-dlp හරහා සුපිරියටම බාගැනීම
        os.system(f'yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 "{req.url}" -o "{filename}"')
        if not os.path.exists(filename):
            raise HTTPException(status_code=500, detail="බාගැනීම අසාර්ථක විය!")
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

    # Colab සර්වර් එක ඇතුළේ background එකේ Chrome එකක් සකස් කිරීම
    chrome_options = Options()
    chrome_options.add_argument("--headless") # අපිට නොපෙනී background එකේ දුවන්න
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 1. Google Login පිටුවට යාම
        driver.get("https://accounts.google.com/ServiceLogin?service=youtube")
        time.sleep(3)
        
        # Email එක ඇතුළත් කිරීම
        email_field = driver.find_element(By.NAME, "identifier")
        email_field.send_keys(req.email)
        driver.find_element(By.ID, "identifierNext").click()
        time.sleep(4)
        
        # Password එක ඇතුළත් කිරීම
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(req.password)
        driver.find_element(By.ID, "passwordNext").click()
        time.sleep(6)
        
        # 2. YouTube Studio උඩුගත කිරීමේ පිටුවට යාම
        driver.get("https://studio.youtube.com/channel/UC/videos?d=ud")
        time.sleep(5)
        
        # වීඩියෝ ෆයිල් එක තෝරාගැනීම (File Input එකට සර්වර් එකේ ඇති path එක දීම)
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(full_path)
        time.sleep(5) # වීඩියෝව සර්වර් එකෙන් Studio එකට ලෝඩ් වන තෙක්
        
        # Title එක ඇතුළත් කිරීම (පළමු textbox එක)
        title_box = driver.find_element(By.XPATH, "//div[@id='textbox' and @textbox-id='title-textbox']")
        title_box.clear()
        title_box.send_keys(req.title)
        
        # Description එක ඇතුළත් කිරීම
        desc_box = driver.find_element(By.XPATH, "//div[@id='textbox' and @textbox-id='description-textbox']")
        desc_box.clear()
        desc_box.send_keys(req.description)
        time.sleep(2)
        
        # "Next" බටන් එක 3 පාරක් ක්ලික් කිරීම (Details -> Video Elements -> Checks -> Visibility)
        for _ in range(3):
            next_btn = driver.find_element(By.ID, "next-button")
            next_btn.click()
            time.sleep(3)
            
        # වීඩියෝව Private දැමීම (නැතහොත් Public කිරීමට බටන් වෙනස් කළ හැක)
        private_radio = driver.find_element(By.NAME, "PRIVATE")
        private_radio.click()
        time.sleep(2)
        
        # අවසාන වශයෙන් "Save" බටන් එක ක්ලික් කිරීම
        save_btn = driver.find_element(By.ID, "done-button")
        save_btn.click()
        time.sleep(5) # සම්පූර්ණයෙන් සේව් වන තෙක්
        
        driver.quit()
        
        # ✂️ සර්වර් එකෙන් වීඩියෝව මකා දැමීම
        if os.path.exists(full_path):
            os.remove(full_path)
            
        return {"message": "🔥 සාර්ථකයි! Custom API එකෙන් වීඩියෝව ඔටෝම YouTube එකට දැම්මා, සර්වර් එකෙනුත් කැපුනා!"}
        
    except Exception as e:
        driver.quit()
        raise HTTPException(status_code=500, detail=f"ලොගින් වීම හෝ අප්ලෝඩ් වීම අසාර්ථකයි: {str(e)}")
