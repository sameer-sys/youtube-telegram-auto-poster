"""
Facebook Reels & Instagram Posting Bot with 2026 Algorithm Tricks
- Facebook: 3-5 relevant hashtags, question caption, daily posting, no watermarks
- Instagram: Keywords first line, 5-8 hashtags (branding only)
- Freshness boost: Same-day uploads get 50% more distribution
"""

import os
import json
import asyncio
import logging
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from enum import Enum

import aiofiles
import requests
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.advideo import AdVideo as Video
from facebook_business.adobjects.iguser import IGUser
from facebook_business.adobjects.igmedia import IGMedia

# ==================== CONFIG ====================
FB_CONFIG_FILE = 'fb_config.json'
FB_METADATA_DIR = Path('fb_metadata')
IG_METADATA_DIR = Path('ig_metadata')
LOG_FILE = 'fb_ig_posting_bot.log'

# Facebook Reels 2026 Tricks Config
FB_CONFIG = {
    'hashtag_count': 5,  # 3-5 relevant hashtags
    'caption_max_chars': 2200,
    'post_daily': True,
    'freshness_boost_hours': 24,  # Same-day uploads get 50% more distribution
    'ask_question_in_caption': True,
    'no_watermark_required': True,
}

# Instagram Config (branding only)
IG_CONFIG = {
    'hashtag_count': 8,  # 5-8 hashtags
    'keywords_first_line': True,
    'caption_max_chars': 2200,
}

# Posting times (IST)
FB_POST_TIMES = [time(7, 0), time(17, 0)]  # 7 AM and 5 PM IST
IG_POST_TIMES = [time(9, 0), time(19, 0)]  # 9 AM and 7 PM IST

IST_OFFSET = timedelta(hours=5, minutes=30)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== DATA MODELS ====================
class Platform(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


@dataclass
class PostMetadata:
    platform: str
    video_path: str
    caption: str
    hashtags: List[str]
    thumbnail_path: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    status: str = 'pending'  # pending, posted, failed
    post_id: Optional[str] = None
    error: Optional[str] = None
    ai_generated: bool = True


# ==================== FACEBOOK API HELPER ====================
class FacebookPoster:
    def __init__(self, config: Dict):
        self.config = config
        self.access_token = config.get('page_access_token')
        self.page_id = config.get('page_id')
        self.app_id = config.get('app_id')
        self.app_secret = config.get('app_secret')
        
        if self.access_token and self.app_id and self.app_secret:
            FacebookAdsApi.init(self.app_id, self.app_secret, self.access_token)
            logger.info("Facebook API initialized")

    def upload_reel(self, metadata: PostMetadata) -> Optional[str]:
        """Upload video as Facebook Reel"""
        try:
            page = Page(self.page_id)
            
            # Build caption with question and hashtags
            full_caption = self._build_caption(metadata.caption, metadata.hashtags)
            
            # Upload video (local file or URL)
            if os.path.exists(metadata.video_path):
                with open(metadata.video_path, 'rb') as f:
                    video = page.create_video(
                        params={
                            'description': full_caption,
                            'title': metadata.caption[:100],
                        },
                        files={'source': f}
                    )
            else:
                video = page.create_video(
                    params={
                        'file_url': metadata.video_path,
                        'description': full_caption,
                        'title': metadata.caption[:100],
                    }
                )
            
            video_id = video['id']
            logger.info(f"Facebook Reel uploaded: {video_id}")
            
            # Wait for processing and publish as Reel
            self._publish_reel(video_id, full_caption)
            
            return video_id
            
        except Exception as e:
            logger.error(f"Facebook upload error: {e}")
            raise

    def _build_caption(self, caption: str, hashtags: List[str]) -> str:
        """Build caption with question + 3-5 hashtags"""
        hashtag_list = hashtags[:FB_CONFIG['hashtag_count']]
        hashtag_str = ' '.join([f'#{tag}' for tag in hashtag_list])
        
        # Add question to prompt comments (strong signal)
        question = ""
        if FB_CONFIG['ask_question_in_caption']:
            questions = [
                "What do you think? 🤔",
                "Which one is your favorite? 👇",
                "Tag a friend who needs to see this! 😂",
                "Agree or disagree? 💭",
                "What would you do? 🤷‍♂️"
            ]
            import random
            question = f"\n\n{random.choice(questions)}"
        
        full_caption = f"{caption}{question}\n\n{hashtag_str}"
        
        if len(full_caption) > FB_CONFIG['caption_max_chars']:
            full_caption = full_caption[:FB_CONFIG['caption_max_chars'] - 3] + '...'
        
        return full_caption

    def _publish_reel(self, video_id: str, caption: str):
        """Publish video as Reel"""
        try:
            video = Video(video_id)
            video.api_put(
                fields=[],
                params={
                    'published': True,
                    'description': caption,
                }
            )
            logger.info(f"Facebook Reel published: {video_id}")
        except Exception as e:
            logger.error(f"Reel publish error: {e}")
            raise


# ==================== INSTAGRAM API HELPER ====================
class InstagramPoster:
    def __init__(self, config: Dict):
        self.config = config
        self.access_token = config.get('ig_access_token')
        self.ig_user_id = config.get('ig_user_id')
        self.app_id = config.get('app_id')
        self.app_secret = config.get('app_secret')
        
        if self.access_token and self.app_id and self.app_secret:
            FacebookAdsApi.init(self.app_id, self.app_secret, self.access_token)
            logger.info("Instagram API initialized")

    def upload_reel(self, metadata: PostMetadata) -> Optional[str]:
        """Upload video as Instagram Reel"""
        try:
            ig_user = IGUser(self.ig_user_id)
            
            # Build caption: keywords first line + hashtags
            full_caption = self._build_caption(metadata.caption, metadata.hashtags)
            
            # Create media container
            media = ig_user.create_media(
                params={
                    'media_type': 'REELS',
                    'video_url': metadata.video_path,  # Must be publicly accessible URL
                    'caption': full_caption,
                    'share_to_feed': True,
                }
            )
            
            media_id = media['id']
            
            # Publish
            publish_result = ig_user.create_media_publish(
                params={
                    'creation_id': media_id,
                }
            )
            
            post_id = publish_result['id']
            logger.info(f"Instagram Reel published: {post_id}")
            return post_id
            
        except Exception as e:
            logger.error(f"Instagram upload error: {e}")
            raise

    def _build_caption(self, caption: str, hashtags: List[str]) -> str:
        """Build caption: keywords first line + 5-8 hashtags"""
        hashtag_list = hashtags[:IG_CONFIG['hashtag_count']]
        hashtag_str = ' '.join([f'#{tag}' for tag in hashtag_list])
        
        if IG_CONFIG['keywords_first_line']:
            # First line should contain main keywords
            first_line = caption.split('\n')[0] if caption else "AI Cartoon"
            remaining = '\n'.join(caption.split('\n')[1:]) if '\n' in caption else ""
            full_caption = f"{first_line}\n\n{remaining}\n\n{hashtag_str}".strip()
        else:
            full_caption = f"{caption}\n\n{hashtag_str}"
        
        if len(full_caption) > IG_CONFIG['caption_max_chars']:
            full_caption = full_caption[:IG_CONFIG['caption_max_chars'] - 3] + '...'
        
        return full_caption


# ==================== SCHEDULER ====================
class FBScheduler:
    def __init__(self, poster: FacebookPoster):
        self.poster = poster
        self.running = False

    def get_next_post_time(self) -> datetime:
        """Get next posting time (7 AM or 5 PM IST)"""
        now_utc = datetime.utcnow()
        now_ist = now_utc + IST_OFFSET
        
        for post_time in FB_POST_TIMES:
            next_post = now_ist.replace(hour=post_time.hour, minute=post_time.minute, second=0, microsecond=0)
            if now_ist < next_post:
                return next_post - IST_OFFSET
        
        # Next day 7 AM
        next_post = (now_ist + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
        return next_post - IST_OFFSET

    async def process_pending(self):
        metadata_files = sorted(FB_METADATA_DIR.glob('*.json'))
        
        for meta_file in metadata_files:
            async with aiofiles.open(meta_file, 'r') as f:
                data = json.loads(await f.read())
            
            metadata = PostMetadata(**data)
            
            if metadata.status == 'pending':
                await self.post_now(metadata, meta_file)

    async def post_now(self, metadata: PostMetadata, meta_file: Path):
        try:
            logger.info(f"Posting to Facebook: {metadata.video_path}")
            
            post_id = self.poster.upload_reel(metadata)
            if not post_id:
                raise Exception("Post failed - no post ID returned")
            
            metadata.post_id = post_id
            metadata.status = 'posted'
            metadata.scheduled_time = datetime.utcnow()
            
            async with aiofiles.open(meta_file, 'w') as f:
                await f.write(json.dumps(asdict(metadata), default=str, indent=2))
            
            logger.info(f"Facebook Reel posted successfully: {post_id}")
            
        except Exception as e:
            metadata.status = 'failed'
            metadata.error = str(e)
            async with aiofiles.open(meta_file, 'w') as f:
                await f.write(json.dumps(asdict(metadata), default=str, indent=2))
            logger.error(f"Failed to post to Facebook: {e}")

    async def run_loop(self, interval_seconds: int = 600):
        self.running = True
        logger.info("Starting Facebook Reels posting loop...")
        
        while self.running:
            try:
                await self.process_pending()
            except Exception as e:
                logger.error(f"Loop error: {e}")
            
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.running = False


class IGScheduler:
    def __init__(self, poster: InstagramPoster):
        self.poster = poster
        self.running = False

    def get_next_post_time(self) -> datetime:
        now_utc = datetime.utcnow()
        now_ist = now_utc + IST_OFFSET
        
        for post_time in IG_POST_TIMES:
            next_post = now_ist.replace(hour=post_time.hour, minute=post_time.minute, second=0, microsecond=0)
            if now_ist < next_post:
                return next_post - IST_OFFSET
        
        next_post = (now_ist + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        return next_post - IST_OFFSET

    async def process_pending(self):
        metadata_files = sorted(IG_METADATA_DIR.glob('*.json'))
        
        for meta_file in metadata_files:
            async with aiofiles.open(meta_file, 'r') as f:
                data = json.loads(await f.read())
            
            metadata = PostMetadata(**data)
            
            if metadata.status == 'pending':
                await self.post_now(metadata, meta_file)

    async def post_now(self, metadata: PostMetadata, meta_file: Path):
        try:
            logger.info(f"Posting to Instagram: {metadata.video_path}")
            
            post_id = self.poster.upload_reel(metadata)
            if not post_id:
                raise Exception("Post failed - no post ID returned")
            
            metadata.post_id = post_id
            metadata.status = 'posted'
            metadata.scheduled_time = datetime.utcnow()
            
            async with aiofiles.open(meta_file, 'w') as f:
                await f.write(json.dumps(asdict(metadata), default=str, indent=2))
            
            logger.info(f"Instagram Reel posted successfully: {post_id}")
            
        except Exception as e:
            metadata.status = 'failed'
            metadata.error = str(e)
            async with aiofiles.open(meta_file, 'w') as f:
                await f.write(json.dumps(asdict(metadata), default=str, indent=2))
            logger.error(f"Failed to post to Instagram: {e}")

    async def run_loop(self, interval_seconds: int = 600):
        self.running = True
        logger.info("Starting Instagram posting loop...")
        
        while self.running:
            try:
                await self.process_pending()
            except Exception as e:
                logger.error(f"Loop error: {e}")
            
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.running = False


# ==================== METADATA GENERATORS ====================
def generate_fb_metadata(video_path: str, caption: str, hashtags: List[str],
                         thumbnail_path: Optional[str] = None) -> PostMetadata:
    return PostMetadata(
        platform='facebook',
        video_path=video_path,
        caption=caption,
        hashtags=hashtags[:5],  # Max 5
        thumbnail_path=thumbnail_path,
        ai_generated=True,
        status='pending'
    )


def generate_ig_metadata(video_path: str, caption: str, hashtags: List[str],
                         thumbnail_path: Optional[str] = None) -> PostMetadata:
    return PostMetadata(
        platform='instagram',
        video_path=video_path,
        caption=caption,
        hashtags=hashtags[:8],  # Max 8
        thumbnail_path=thumbnail_path,
        ai_generated=True,
        status='pending'
    )


def save_fb_metadata(metadata: PostMetadata, filename: str):
    FB_METADATA_DIR.mkdir(exist_ok=True)
    filepath = FB_METADATA_DIR / f"{filename}.json"
    with open(filepath, 'w') as f:
        json.dump(asdict(metadata), f, default=str, indent=2)
    logger.info(f"FB Metadata saved: {filepath}")
    return filepath


def save_ig_metadata(metadata: PostMetadata, filename: str):
    IG_METADATA_DIR.mkdir(exist_ok=True)
    filepath = IG_METADATA_DIR / f"{filename}.json"
    with open(filepath, 'w') as f:
        json.dump(asdict(metadata), f, default=str, indent=2)
    logger.info(f"IG Metadata saved: {filepath}")
    return filepath


# ==================== CONFIG LOADER ====================
def load_fb_config() -> Dict:
    if os.path.exists(FB_CONFIG_FILE):
        with open(FB_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def create_sample_config():
    """Create sample config file"""
    sample = {
        "page_access_token": "YOUR_PAGE_ACCESS_TOKEN",
        "page_id": "YOUR_PAGE_ID",
        "app_id": "YOUR_APP_ID",
        "app_secret": "YOUR_APP_SECRET",
        "ig_access_token": "YOUR_IG_ACCESS_TOKEN",
        "ig_user_id": "YOUR_IG_USER_ID"
    }
    with open(FB_CONFIG_FILE, 'w') as f:
        json.dump(sample, f, indent=2)
    logger.info(f"Sample config created: {FB_CONFIG_FILE}")


# ==================== MAIN ====================
async def main():
    FB_METADATA_DIR.mkdir(exist_ok=True)
    IG_METADATA_DIR.mkdir(exist_ok=True)
    
    config = load_fb_config()
    
    if not config:
        create_sample_config()
        logger.error("Please fill in fb_config.json with your credentials")
        return
    
    fb_poster = FacebookPoster(config)
    ig_poster = InstagramPoster(config)
    
    fb_scheduler = FBScheduler(fb_poster)
    ig_scheduler = IGScheduler(ig_poster)
    
    # Example: Create metadata for a video (run once per video)
    """
    fb_meta = generate_fb_metadata(
        video_path='https://your-cdn.com/video.mp4',
        caption='AI Cat learns coding in 30 seconds! 🐱💻',
        hashtags=['AI', 'coding', 'cats', 'tech', 'funny'],
        thumbnail_path='https://your-cdn.com/thumb.jpg'
    )
    save_fb_metadata(fb_meta, 'ai_cat_coding')
    
    ig_meta = generate_ig_metadata(
        video_path='https://your-cdn.com/video.mp4',
        caption='AI Cat Coding Tutorial',
        hashtags=['AI', 'coding', 'cats', 'tech', 'funny', 'programming', 'python', 'tutorial'],
        thumbnail_path='https://your-cdn.com/thumb.jpg'
    )
    save_ig_metadata(ig_meta, 'ai_cat_coding')
    """
    
    # Run both schedulers
    await asyncio.gather(
        fb_scheduler.run_loop(interval_seconds=600),
        ig_scheduler.run_loop(interval_seconds=600)
    )


if __name__ == '__main__':
    asyncio.run(main())