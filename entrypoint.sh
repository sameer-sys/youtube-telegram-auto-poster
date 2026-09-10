#!/bin/bash
set -e

# Decode base64 secrets if provided
if [ -n "$CREDENTIALS_JSON_B64" ]; then
    echo "$CREDENTIALS_JSON_B64" | base64 -d > /app/credentials.json
    echo "✅ credentials.json decoded"
fi
if [ -n "$TOKEN_JSON_B64" ]; then
    echo "$TOKEN_JSON_B64" | base64 -d > /app/token.json
    echo "✅ token.json decoded"
fi
if [ -n "$FB_CONFIG_JSON_B64" ]; then
    echo "$FB_CONFIG_JSON_B64" | base64 -d > /app/fb_config.json
    echo "✅ fb_config.json decoded"
fi

# If volume mounted, copy from there (fallback)
if [ -d "/app/secrets" ]; then
    cp -n /app/secrets/* /app/ 2>/dev/null || true
    echo "✅ Volume secrets copied"
fi

# Verify required files exist
for f in credentials.json token.json fb_config.json; do
    if [ ! -f "/app/$f" ]; then
        echo "⚠️  Missing: $f"
    else
        echo "✅ Found: $f"
    fi
done

exec python auto_poster.py