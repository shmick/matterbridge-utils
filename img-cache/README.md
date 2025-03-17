# Discord Image Cache Service

A FastAPI-based service that caches Discord image attachments to Cloudflare R2 storage, making them permanently available through a CDN.

## Features

- Caches images from Discord CDN URLs to Cloudflare R2 storage
- Supports common image formats (jpg, jpeg, png, gif, webp)
- Generates short hashes for cached files
- Handles rate limiting with automatic retries
- Provides modified message content with cached URLs

## How It Works

1. The service accepts POST requests to `/cache` with Discord image URLs
2. Validates if the URL is from Discord's CDN
3. Downloads the image with retry capability
4. Generates a unique short hash for the file
5. Uploads the image to Cloudflare R2 storage
6. Returns a response with both original and cached URLs

## Environment Variables

Required environment variables:
- `CDN_BASE_URL`: Base URL for your CDN
- `R2_ACCOUNT_ID`: Cloudflare R2 account ID
- `R2_ACCESS_KEY_ID`: R2 access key ID
- `R2_SECRET_ACCESS_KEY`: R2 secret access key
- `R2_BUCKET_NAME`: R2 bucket name

## API Endpoints

### POST /cache

Request body:
```json
{
    "message": "Original message containing Discord URL",
    "url": "https://cdn.discordapp.com/attachments/..."
}
```
Response:
```json
{
    "status": "success",
    "cached_url": "https://your-cdn.com/i/filename.ext",
    "original_url": "Original Discord URL",
    "original_message": "Original message",
    "modified_message": "Message with replaced URL",
    "hash": "Short hash",
    "path": "i/filename.ext"
}
```

## Add to docker-compose.yml

```yaml
version: '3.7'
services:
  matterbridge:
    <config>

  img-cache:
    build: 
      context: ./img-cache  # Directory containing Dockerfile and source
      dockerfile: Dockerfile
    ports:
      - "6161:6161"
    environment:
      - R2_ACCOUNT_ID=...
      - R2_ACCESS_KEY_ID=...
      - R2_SECRET_ACCESS_KEY=...
      - R2_BUCKET_NAME=...
      - CDN_BASE_URL=...
    restart: unless-stopped
