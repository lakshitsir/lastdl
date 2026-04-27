import os
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from yt_dlp import YoutubeDL

app = FastAPI()

def get_proxy() -> str | None:
    return os.getenv("YTDL_PROXY")

@app.get("/api/download")
async def get_download(url: str = Query(..., description="Instagram/YouTube/TikTok/Other URL")):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "socket_timeout": 12,
        "retries": 3,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "proxy": get_proxy(),
        # 🔥 प्रायोरिटी: सिंगल MP4 फाइल (ऑडियो+वीडियो साथ में), फॉलबैक बेस्ट अवेलेबल
        "format": "best[ext=mp4][height<=720]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "no_playlists": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # yt-dlp सेलेक्ट किए हुए फॉर्मेट का डायरेक्ट URL
        direct_url = info.get("url")
        format_note = info.get("format", "Unknown")
        
        # अगर डैश/मल्टीफॉर्मेट है, तो पहला उपलब्ध सिंगल यूआरएल लो
        if not direct_url and info.get("formats"):
            direct_url = next((f["url"] for f in info["formats"] if f.get("vcodec") != "none" and f.get("acodec") != "none"), info["formats"][0].get("url"))

        return JSONResponse({
            "status": "success",
            "developer": "Lakshit_API_v1",
            "platform": info.get("extractor", "unknown"),
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration_sec": info.get("duration"),
            "download_url": direct_url,
            "format_info": format_note,
            "note": "Single file with audio+video. Link expires in few hours. Use immediately."
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "developer": "Lakshit_API_v1",
            "message": "Extraction failed. Check URL or try again."
        }, status_code=400)
