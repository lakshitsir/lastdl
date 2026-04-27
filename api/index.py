from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from yt_dlp import YoutubeDL

app = FastAPI()

# 🔒 इन्बिल्ट ब्राउज़र हेडर्स (बॉट ब्लॉकिंग से बचने के लिए)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "no-cache"
}

# 🌐 फॉलबैक प्रॉक्सी लिस्ट (ऑटो रोटेशन, अगर एक फेल हुआ तो अगला ट्राई करेगा)
PROXY_LIST = [
    "http://103.152.112.162:80",
    "http://103.148.24.230:8080",
    "http://47.243.108.68:8080",
    None  # आखिरी में डायरेक्ट कनेक्शन (बिना प्रॉक्सी)
]

def extract_info(url: str, proxy: str | None = None) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "socket_timeout": 8,
        "retries": 2,
        "extractor_retries": 2,
        "geo_bypass": True,
        "no_check_certificate": True,
        "http_headers": HEADERS,
        "proxy": proxy,
        # 🎯 प्रायोरिटी: सिंगल फाइल जहाँ ऑडियो+वीडियो दोनों हों (360p-720p MP4)
        "format": "best[ext=mp4][height<=720]/best[ext=mp4]/best",
        "no_playlists": True,
        "skip_download": True
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

@app.get("/api/download")
async def get_download(url: str = Query(..., description="Instagram/YouTube/TikTok/Other URL")):
    if not url.startswith(("http://", "https://")):
        return JSONResponse({"status": "error", "developer": "Lakshit_API_v1", "message": "Invalid URL"}, status_code=400)

    last_err = None
    info = None

    # 🔁 ऑटो प्रॉक्सी रोटेशन + फॉलबैक
    for proxy in PROXY_LIST:
        try:
            info = extract_info(url, proxy)
            break
        except Exception as e:
            last_err = str(e)
            continue

    if not info:
        return JSONResponse({
            "status": "error",
            "developer": "Lakshit_API_v1",
            "message": "Extraction failed. Try again later."
        }, status_code=400)

    # 📥 डायरेक्ट लिंक निकालना (ऑडियो+वीडियो एक साथ)
    direct_url = info.get("url")
    if not direct_url and info.get("formats"):
        for fmt in info["formats"]:
            if fmt.get("vcodec") != "none" and fmt.get("acodec") != "none" and fmt.get("url"):
                direct_url = fmt["url"]
                break
        if not direct_url:
            direct_url = info["formats"][0].get("url")

    return JSONResponse({
        "status": "success",
        "developer": "Lakshit_API_v1",
        "platform": info.get("extractor", "unknown"),
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration_sec": info.get("duration"),
        "download_url": direct_url,
        "format_note": info.get("format", "auto"),
        "note": "Single file (Audio+Video). Link expires in hours. Download immediately."
    })
