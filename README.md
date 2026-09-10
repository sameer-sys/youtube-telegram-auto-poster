# Posting Bot - YouTube Shorts, Facebook Reels & Instagram

Automated posting bot with 2026 algorithm tricks for monetization.

## Features

### YouTube Shorts (`telegram_loop.py`)
- ✅ **Private at night → Public at 09:00 IST** flip strategy
- ✅ **AI Content Disclosure** (Altered Content toggle) - REQUIRED for YPP
- ✅ **Title < 60 chars** with hook + 1-5 relevant hashtags
- ✅ **Pin comment** after upload for early engagement
- ✅ **Hide likes** (`publicStatsViewable: false`)
- ✅ **Correct encoding**: 1080x1920, H.264, AAC 192kbps
- ✅ **No #shorts #viral #fyp** - uses topic/audience/market hashtags

### Facebook Reels (`fb_ig.py`)
- ✅ **3-5 relevant hashtags** (not 30)
- ✅ **Question in caption** to prompt comments (strong signal)
- ✅ **Daily posting** at 7 AM & 5 PM IST
- ✅ **Freshness boost**: Same-day uploads get 50% more distribution
- ✅ **No watermarks** required
- ✅ **Monetization target**: 5K followers + 60K min viewed/60 days

### Instagram (`fb_ig.py`) - Branding Only
- ✅ **Keywords first line** for categorization
- ✅ **5-8 hashtags**
- ✅ **Posting at 9 AM & 7 PM IST**

### Telegram Bot (`telegram_bot.py`) - NEW!
- ✅ **Send video directly to Telegram** → auto-queues for all platforms
- ✅ **Interactive metadata collection** (title, description, hashtags)
- ✅ **Choose platforms** (All / YouTube / Facebook / Instagram)
- ✅ **Queue status** with `/status` command

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. YouTube API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `credentials.json` in project root
5. Run once to authorize:
```bash
python telegram_loop.py
```
This creates `token.json` for future runs.

### 3. Facebook/Instagram Setup
1. Create [Meta App](https://developers.facebook.com/apps/)
2. Add Facebook Login, Instagram Basic Display, Pages permissions
3. Get Page Access Token (long-lived, 60 days)
4. Get Instagram User ID
5. Fill in `fb_config.json`

### 4. Telegram Bot Setup
1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copy the bot token
3. Set environment variables:
```bash
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:ADMIN_USER_IDS="123456789,987654321"  # Your Telegram user IDs (comma-separated)

# Or create .env file:
echo TELEGRAM_BOT_TOKEN=your_bot_token_here > .env
echo ADMIN_USER_IDS=123456789,987654321 >> .env
```
4. Get your user ID: message [@userinfobot](https://t.me/userinfobot)

### 5. Video Requirements
- **Resolution**: 1080x1920 (9:16)
- **Codec**: H.264 video, AAC audio 192kbps stereo
- **Format**: MP4
- **Duration**: 15-60 seconds (YT), 15-90 seconds (FB/IG)
- **No watermarks** (TikTok, CapCut, etc.)

## Usage

### Option A: Telegram Bot (Easiest)
```bash
# Terminal 1: Start Telegram bot
python telegram_bot.py

# Terminal 2: Start YouTube loop
python telegram_loop.py

# Terminal 3: Start FB/IG loop
python fb_ig.py
```
Then in Telegram:
1. Send video to your bot
2. Enter title → description → hashtags
3. Choose platforms → queued automatically!

### Option B: Manual Metadata (Original Way)
```python
from telegram_loop import generate_metadata, save_metadata

meta = generate_metadata(
    video_path='videos/my_short.mp4',
    title='AI Cat Learns Coding in 30 Seconds',
    description='Watch this AI cat master Python! 🐱💻',
    hashtags=['AI', 'coding', 'cats', 'tech', 'funny'],
    ai_generated=True,
    thumbnail_path='videos/my_short_thumb.jpg'
)
save_metadata(meta, 'my_short')
```

### Run the Loop Bots
```bash
# YouTube Shorts (runs continuously, checks every 5 min)
python telegram_loop.py

# Facebook + Instagram (runs continuously, checks every 10 min)
python fb_ig.py
```

### Directory Structure
```
├── telegram_bot.py           # Telegram bot (NEW!)
├── telegram_loop.py          # YouTube Shorts loop bot
├── fb_ig.py                  # Facebook & Instagram loop bot
├── requirements.txt
├── credentials.json          # YouTube OAuth (you provide)
├── token.json                # YouTube token (auto-generated)
├── fb_config.json            # FB/IG credentials (you provide)
├── .env                      # Telegram token + admin IDs (you provide)
├── videos/                   # Your video files
├── metadata/                 # YouTube metadata JSONs
├── fb_metadata/              # Facebook metadata JSONs
├── ig_metadata/              # Instagram metadata JSONs
├── posting_bot.log           # YouTube logs
├── fb_ig_posting_bot.log     # FB/IG logs
└── telegram_bot.log          # Telegram bot logs
```

## 2026 Algorithm Tricks Applied

| Trick | Platform | Implementation |
|-------|----------|----------------|
| Private→Public flip | YT | Upload private at night, auto-publish 09:00 IST |
| AI Disclosure | YT | `alteredContent: true` in status |
| Pin Comment | YT | Auto-pins engagement bait comment |
| Hide Likes | YT | `publicStatsViewable: false` |
| Smart Hashtags | YT/FB/IG | 1-5 (YT), 3-5 (FB), 5-8 (IG) relevant tags |
| Question Caption | FB | Random engagement question appended |
| Keywords First Line | IG | First line = main keywords |
| Daily Posting | FB/IG | 2x/day scheduled times |
| Freshness Boost | FB | Same-day upload priority |

## Monetization Checklist

### YouTube (YPP)
- [ ] 1,000 subscribers
- [ ] 10M Shorts views in 90 days
- [ ] AI disclosure enabled ✅
- [ ] No copyright strikes

### Facebook (FCM)
- [ ] 5,000 followers
- [ ] 60,000 minutes viewed in 60 days
- [ ] Original content (no watermarks) ✅
- [ ] 3-5 Reels/week minimum ✅

### Instagram
- Branding only - no monetization focus

## Logs
Check `posting_bot.log`, `fb_ig_posting_bot.log`, and `telegram_bot.log` for status.

## Troubleshooting
- **YouTube quota exceeded**: Wait 24h, reduce upload frequency
- **FB token expired**: Regenerate long-lived token
- **Video rejected**: Check encoding (H.264/AAC), no watermarks
- **Low views**: Improve hook (first 1-2s), add loop ending
- **Telegram bot not responding**: Check TELEGRAM_BOT_TOKEN and ADMIN_USER_IDS