# OmniRoute Cloud Service

Lightweight OpenAI-compatible cloud proxy for OpenWork and AI agents.

## Features
- OpenAI compatible API: `/v1/models` and `/v1/chat/completions`
- Compatible with OpenWork Desktop & OpenCode
- Standalone zero-dependency Node.js service
- Built-in `/health` check for Render, Railway, Koyeb, Fly.io, etc.

## Deploying to Render (Free)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** -> **Web Service**
3. Connect your GitHub repository (`sameer-sys/omniroute` or `sameer-sys/youtube-telegram-auto-poster`)
4. Settings:
   - **Environment**: `Node`
   - **Build Command**: `npm install` (or leave empty)
   - **Start Command**: `npm start`
5. Click **Create Web Service**
6. Copy your public HTTPS URL (e.g. `https://omniroute-cloud.onrender.com`)
