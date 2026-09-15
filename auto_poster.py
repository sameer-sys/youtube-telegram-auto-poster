import os
import sys
import json
import logging
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# FB/IG integration
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fb_ig import FacebookPoster, InstagramPoster, generate_fb_metadata, generate_ig_metadata, save_fb_metadata, save_ig_metadata, load_fb_config

# Load .env
def load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_USER_IDS = os.environ.get("ADMIN_USER_IDS", "").split(",")

# Cloud-friendly: YouTube creds from env (JSON) or token.json file
def get_youtube_creds():
    if os.environ.get("YOUTUBE_TOKEN_JSON"):
        return json.loads(os.environ["YOUTUBE_TOKEN_JSON"])
    with open("token.json", "r") as f:
        return json.load(f)

logging.basicConfig(filename="bot_activity.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class YouTubePoster:
    def __init__(self):
        self.token_path = "token.json"

    def get_service(self):
        token_data = get_youtube_creds()
        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret")
        )
        return build("youtube", "v3", credentials=creds)

    def upload(self, file_path, title="AI Uploaded Video", desc="Posted via Auto-Poster Bot"):
        try:
            youtube = self.get_service()
            body = {
                "snippet": {"title": title, "description": desc, "categoryId": "22"},
                "status": {"privacyStatus": "public"}
            }
            # Simple upload without progress tracking to avoid the "tuple" error
            media = MediaFileUpload(file_path)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = request.execute()
            
            return f"https://www.youtube.com/watch?v={response['id']}"
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return None

class AutoPoster:
    def __init__(self):
        self.yt = YouTubePoster()
        self.fb_config = load_fb_config()
        self.fb_poster = FacebookPoster(self.fb_config) if self.fb_config.get('page_access_token') else None
        self.ig_poster = InstagramPoster(self.fb_config) if self.fb_config.get('ig_access_token') else None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Bot is online! Send me a video.")

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if user_id not in ADMIN_USER_IDS and "YOUR_USER_ID_HERE" in ADMIN_USER_IDS:
            return

        logger.info(f"Processing video from {user_id}")
        await update.message.reply_text("Video received! Uploading to YouTube, Facebook & Instagram...")
        
        try:
            video_file = await update.message.video.get_file()
            file_path = f"temp_{user_id}_{video_file.file_id}.mp4"
            await video_file.download_to_drive(file_path)
            
            caption = update.message.caption or "AI Cartoon Video"
            hashtags = ["AI", "cartoon", "animation", "funny", "viral", "trending", "reels", "shorts"]
            
            # 1. YouTube
            url = self.yt.upload(file_path, title=caption[:100], desc=caption)
            
            # 2. Facebook Reel (auto-cross-posts to Instagram)
            fb_result = None
            if self.fb_poster:
                try:
                    fb_meta = generate_fb_metadata(file_path, caption, hashtags)
                    fb_result = self.fb_poster.upload_reel(fb_meta)
                except Exception as e:
                    logger.error(f"FB upload error: {e}")
                    fb_result = f"FAILED: {e}"
            
            # 3. Instagram Reel (direct IG API via public URL)
            ig_result = "SKIPPED"
            if self.ig_poster:
                try:
                    ig_meta = generate_ig_metadata(file_path, caption, hashtags)
                    ig_result = self.ig_poster.upload_reel(ig_meta)
                except Exception as e:
                    logger.error(f"IG upload error: {e}")
                    ig_result = f"FAILED: {e}"
            
            reply = f"YouTube: {url if url else 'FAILED'}\n"
            reply += f"Facebook: {fb_result if fb_result else 'SKIPPED'}\n"
            reply += f"Instagram: {ig_result if ig_result else 'SKIPPED'}"
            await update.message.reply_text(reply)
            
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Bot handle_video error: {e}")
            await update.message.reply_text(f"Error: {e}")

def main():
    if not BOT_TOKEN:
        print("No BOT_TOKEN")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    poster = AutoPoster()
    app.add_handler(CommandHandler("start", poster.start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, poster.handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
