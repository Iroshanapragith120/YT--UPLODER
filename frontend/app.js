// Sidebar toggle (ඇරීම සහ වැසීම)
function toggleMenu() {
    const sidebar = document.getElementById("sidebar");
    if (sidebar.style.width === "300px") {
        sidebar.style.width = "0";
    } else {
        sidebar.style.width = "300px";
    }
}

// පිටු අතර මාරු වීම (Navigation)
function showSection(sectionId) {
    document.getElementById("home-section").classList.add("hidden");
    document.getElementById("download-page").classList.add("hidden");
    
    // අවශ්‍ය පිටුව විතරක් පෙන්වන්න
    document.getElementById(sectionId).classList.remove("hidden");
    
    // සයිඩ් බාර් එක වැසීම
    document.getElementById("sidebar").style.width = "0";
}

// වීඩියෝ එක ඩවුන්ලෝඩ් කරන්න පටන් ගන්න බටන් එක එබුවම
function startDownload() {
    const url = document.getElementById("video-link").value.trim();
    const customName = document.getElementById("custom-name").value.trim();
    
    if(!url) {
        alert("කරුණාකර වීඩියෝ ලින්ක් එක දාන්න මචන්!");
        return;
    }
    
    alert(`ඩවුන්ලෝඩ් එක පටන් ගත්තා!\nනම: ${customName ? customName : "මුල් නම"}\n\nදැන් backend එකට ඩේටා යවනවා...`);
    // මෙතනින් Backend (Python) එකට ඩේටා යවන API එක ඊළඟ පියවරේදී සම්බන්ධ කරනවා.
}
