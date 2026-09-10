#!/bin/bash
# deploy.sh - One-command deploy to any Ubuntu VPS (Oracle, DigitalOcean, Linode, etc.)
# Usage: ./deploy.sh user@your-server-ip

set -e

SERVER=${1:-"ubuntu@your-server-ip"}
PROJECT_DIR="/home/ubuntu/auto-poster-bot"

echo "🚀 Deploying Auto Poster Bot to $SERVER"

# 1. Copy files to server
echo "📦 Copying project files..."
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='videos/*' \
  --exclude='metadata/*' \
  --exclude='fb_metadata/*' \
  --exclude='ig_metadata/*' \
  . $SERVER:$PROJECT_DIR/

# 2. Run setup on server
echo "🔧 Setting up on server..."
ssh $SERVER << 'ENDSSH'
set -e

cd /home/ubuntu/auto-poster-bot

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker ubuntu
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get update && sudo apt-get install -y docker-compose-plugin
fi

# Create .env from template if not exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env template - YOU MUST EDIT IT WITH YOUR TOKENS!"
    cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_IDS=your_telegram_user_id_here
EOF
fi

# Create required config files if not exist
[ ! -f credentials.json ] && echo '{}' > credentials.json
[ ! -f token.json ] && echo '{}' > token.json
[ ! -f fb_config.json ] && cat > fb_config.json << 'EOF'
{
  "page_access_token": "your_fb_page_token",
  "page_id": "your_fb_page_id",
  "app_id": "your_fb_app_id",
  "app_secret": "your_fb_app_secret",
  "ig_access_token": "your_ig_token",
  "ig_user_id": "your_ig_user_id"
}
EOF

# Build and start
echo "🐳 Building and starting containers..."
docker compose build --no-cache
docker compose up -d

# Show status
docker compose ps
docker compose logs -f --tail=50 auto-poster
ENDSSH

echo "✅ Deploy complete!"
echo ""
echo "📋 Next steps on server:"
echo "  1. Edit configs: ssh $SERVER 'cd $PROJECT_DIR && nano .env credentials.json token.json fb_config.json'"
echo "  2. View logs:    ssh $SERVER 'cd $PROJECT_DIR && docker compose logs -f auto-poster'"
echo "  3. Restart:      ssh $SERVER 'cd $PROJECT_DIR && docker compose restart auto-poster'"
echo "  4. Update:       Run this script again"