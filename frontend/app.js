// 💡 වීඩියෝව ඩවුන්ලෝඩ් වුණාම සර්වර් එකේ සේව් වුණු නම මතක තබා ගැනීමට
let downloadedFileName = "";

// 📥 1. වීඩියෝව සර්වර් එකට බාගැනීමේ ෆන්ක්ෂන් එක
async function downloadVideo() {
    const url = document.getElementById("video-url").value;
    const customName = document.getElementById("custom-name").value;
    const statusDiv = document.getElementById("download-status");

    if (!url) {
        statusDiv.innerHTML = "⚠️ කරුණාකර වීඩියෝ ලින්ක් එකක් ඇතුළත් කරන්න!";
        statusDiv.className = "status-msg error";
        return;
    }

    statusDiv.innerHTML = "⏳ වීඩියෝව සර්වර් එකට බාගනිමින් පවතී... කරුණාකර රැඳී සිටින්න...";
    statusDiv.className = "status-msg info";

    try {
        // 💡 Cloudflare Tunnel එකට ගැළපෙන්න කෙළින්ම Relative Path පාවිච්චි කර ඇත
        const response = await fetch("/download", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: url,
                custom_name: customName
            })
        });

        const data = await response.json();

        if (response.ok) {
            statusDiv.innerHTML = `✅ ${data.message}`;
            statusDiv.className = "status-msg success";
            
            // 💡 සේව් වුණු ෆයිල් එක ඊළඟ පියවරට ඔටෝම සෙට් කරනවා
            // පරිශීලකයා නමක් දුන්නේ නැත්නම් default 'video.mp4' ලෙස ගනී
            let safeName = customName.trim() ? customName.trim() : "video";
            safeName = safeName.replace(/[^a-zA-Z0-9_\- ]/g, ''); // කැත අකුරු අයින් කිරීම
            downloadedFileName = `${safeName}.mp4`;
            
            // යූටියුබ් ටයිටල් එකටත් ඔටෝම ඒ නමම දාලා දෙනවා ලේසි වෙන්න
            document.getElementById("yt-title").value = safeName;
        } else {
            statusDiv.innerHTML = `❌ දෝෂයක් සිදු වුණා: ${data.detail}`;
            statusDiv.className = "status-msg error";
        }
    } catch (error) {
        statusDiv.innerHTML = "❌ සර්වර් එක සමඟ සම්බන්ධ වීමට නොහැක!";
        statusDiv.className = "status-msg error";
        console.error(error);
    }
}

// 🔑 2. YOUTUBE LOGIN ලින්ක් එක ලබාගැනීම
async function getAuthUrl() {
    const authContainer = document.getElementById("auth-url-container");
    const authLink = document.getElementById("auth-link");
    const uploadStatus = document.getElementById("upload-status");

    try {
        // 💡 Relative Path පාවිච්චි කර ඇත
        const response = await fetch("/get-auth-url");
        const data = await response.json();

        if (response.ok) {
            authLink.href = data.auth_url;
            authContainer.style.display = "block";
            uploadStatus.innerHTML = "🔑 කරුණාකර ඉහත ලින්ක් එකෙන් ගොස් ලොග් වී Code එක රැගෙන එන්න.";
            uploadStatus.className = "status-msg info";
        } else {
            uploadStatus.innerHTML = `❌ Config දෝෂයක්: ${data.detail}`;
            uploadStatus.className = "status-msg error";
        }
    } catch (error) {
        uploadStatus.innerHTML = "❌ සර්වර් එක සමඟ සම්බන්ධ වීමට නොහැක!";
        uploadStatus.className = "status-msg error";
    }
}

// 📤 3. YOUTUBE එකට UPLOAD කර සර්වර් එකෙන් CUT (AUTO-DELETE) කිරීම
async function uploadAndCutVideo() {
    const authCode = document.getElementById("auth-code").value;
    const title = document.getElementById("yt-title").value;
    const description = document.getElementById("yt-desc").value;
    const uploadStatus = document.getElementById("upload-status");

    if (!authCode) {
        uploadStatus.innerHTML = "⚠️ කරුණාකර Google Auth Code එක ඇතුළත් කරන්න!";
        uploadStatus.className = "status-msg error";
        return;
    }

    if (!downloadedFileName) {
        uploadStatus.innerHTML = "⚠️ ප්‍රථමයෙන් පළමු පියවරෙන් වීඩියෝවක් ඩවුන්ලෝඩ් කර සිටින්න!";
        uploadStatus.className = "status-msg error";
        return;
    }

    uploadStatus.innerHTML = "⏳ වීඩියෝව YouTube වෙත අප්ලෝඩ් වෙමින් පවතී... සර්වර් එකෙන් මැකී යාමට ආසන්නයි...";
    uploadStatus.className = "status-msg info";

    try {
        // 💡 Relative Path පාවිච්චි කර ඇත
        const response = await fetch("/upload", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                filename: downloadedFileName,
                title: title ? title : "My Uploaded Video",
                description: description ? description : "Uploaded via YT Uploader Web Pro",
                is_series: false, // අවශ්‍ය නම් පසුව සීරීස් ලොජික් දාත හැක
                auth_code: authCode
            })
        });

        const data = await response.json();

        if (response.ok) {
            uploadStatus.innerHTML = `🔥 සාර්ථකයි! වීඩියෝව YouTube වෙත ගියා (ID: ${data.video_id}). සර්වර් එකෙන් සදහටම මැකී ගියා (Cut & Cleaned)!`;
            uploadStatus.className = "status-msg success";
            
            // වැඩේ ඉවර නිසා වේරියබල් එක හිස් කරනවා
            downloadedFileName = "";
        } else {
            uploadStatus.innerHTML = `❌ අප්ලෝඩ් වීමේ දෝෂයක්: ${data.detail}`;
            uploadStatus.className = "status-msg error";
        }
    } catch (error) {
        uploadStatus.innerHTML = "❌ සර්වර් එක සමඟ සම්බන්ධ වීමට නොහැක!";
        uploadStatus.className = "status-msg error";
        console.error(error);
    }
}
