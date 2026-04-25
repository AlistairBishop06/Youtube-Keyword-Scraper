import requests
import time
import os
import smtplib
from email.mime.text import MIMEText
from youtube_transcript_api import YouTubeTranscriptApi

API_KEY = os.environ["YOUTUBE_API_KEY"]
CHANNEL_ID = "UCGmnsW623G1r-Chmo5RB4Yw"
KEYWORDS = ["amazon", "code", "gift card"]

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]

last_video_id = None


def get_latest_video():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": API_KEY,
        "channelId": CHANNEL_ID,
        "part": "snippet",
        "order": "date",
        "maxResults": 1,
    }
    response = requests.get(url, params=params).json()
    items = response.get("items", [])
    if not items:
        return None
    video = items[0]
    video_id = video["id"].get("videoId")
    snippet = video["snippet"]
    title = snippet["title"]
    description = snippet["description"]
    return video_id, title, description


def get_keyword_timestamps(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        print(f"Could not fetch transcript: {e}")
        return []

    matches = []
    for entry in transcript:
        text = entry["text"].lower()
        for keyword in KEYWORDS:
            if keyword.lower() in text:
                seconds = int(entry["start"])
                timestamp = f"{seconds // 60:02d}:{seconds % 60:02d}"
                matches.append((keyword, timestamp, entry["text"]))
    return matches


def send_email(video_id, title, matches):
    lines = [f"Keyword matches in: {title}", f"https://www.youtube.com/watch?v={video_id}", ""]
    for keyword, timestamp, text in matches:
        lines.append(f"[{timestamp}] '{keyword}' — {text}")

    msg = MIMEText("\n".join(lines))
    msg["Subject"] = f"Keyword match found: {title}"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

    print(f"Email sent for: {title}")


def contains_keyword(text):
    text = text.lower()
    for keyword in KEYWORDS:
        if keyword.lower() in text:
            return True
    return False


while True:
    result = get_latest_video()
    if result:
        video_id, title, description = result
        if video_id != last_video_id:
            last_video_id = video_id
            combined_text = title + " " + description
            if contains_keyword(combined_text):
                print("keyword match found:", title)
                matches = get_keyword_timestamps(video_id)
                if matches:
                    send_email(video_id, title, matches)
                else:
                    print("No transcript matches found")
            else:
                print("new video (no keyword):", title)
    time.sleep(10)