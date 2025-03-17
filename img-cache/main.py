from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import hashlib
import os
from urllib.parse import urlparse
import asyncio
from typing import Optional
import boto3
from botocore.config import Config

app = FastAPI()

# Updated Model for the request body
class CacheRequest(BaseModel):
    message: str  # The full message from Matterbridge
    url: str      # The Discord URL to cache

# New Response Model
class CacheResponse(BaseModel):
    status: str
    cached_url: str
    original_url: str
    original_message: str
    modified_message: str
    hash: str
    path: str

# Configure these values for your environment
CDN_BASE_URL = os.getenv('CDN_BASE_URL')
if not CDN_BASE_URL:
    raise ValueError("CDN_BASE_URL environment variable is not set")

# R2 Configuration
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

def get_r2_client():
    return boto3.client('s3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def is_discord_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        valid_domains = {
            'cdn.discordapp.com',
            'media.discordapp.net',
            'images-ext-1.discordapp.net'
        }
        
        if parsed.hostname not in valid_domains:
            return False
            
        return '/attachments/' in parsed.path or '/external/' in parsed.path
    except Exception:
        return False

async def create_short_hash(url: str) -> str:
    # Remove Discord's query parameters for consistent hashing
    parsed = urlparse(url)
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    return hashlib.sha256(clean_url.encode()).hexdigest()[:8]

async def fetch_with_retry(url: str, retries: int = 3) -> Optional[bytes]:
    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < retries - 1:
                    retry_after = int(e.response.headers.get('Retry-After', '1'))
                    await asyncio.sleep(retry_after)
                    continue
                raise HTTPException(status_code=e.response.status_code, 
                                 detail=f"Failed to fetch Discord image: {str(e)}")
            except Exception as e:
                if attempt == retries - 1:
                    raise HTTPException(status_code=500, 
                                     detail=f"Failed to fetch after {retries} attempts: {str(e)}")

@app.post("/cache", response_model=CacheResponse)
async def cache_image(request: CacheRequest):
    if not is_discord_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid Discord URL")

    # Generate hash and determine file extension
    short_hash = await create_short_hash(request.url)
    parsed_url = urlparse(request.url)
    file_ext = os.path.splitext(parsed_url.path)[1].lower()
    
    if not file_ext or file_ext[1:] not in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
        raise HTTPException(status_code=400, detail="Invalid file extension")

    # Fetch the image
    image_data = await fetch_with_retry(request.url)
    
    # Create the path in the /i/ folder
    file_name = f"{short_hash}{file_ext}"
    r2_key = f"i/{file_name}"

    # Map file extensions to content types
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }

    # Upload to R2
    r2_client = get_r2_client()
    try:
        r2_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=r2_key,
            Body=image_data,
            ContentType=content_types.get(file_ext, 'application/octet-stream')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to R2: {str(e)}")

    # Generate the cached URL
    cached_url = f"{CDN_BASE_URL}/{r2_key}"
    
    # Replace the Discord URL with the cached URL in the original message
    modified_message = request.message.replace(request.url, cached_url)

    return CacheResponse(
        status="success",
        cached_url=cached_url,
        original_url=request.url,
        original_message=request.message,
        modified_message=modified_message,
        hash=short_hash,
        path=r2_key
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6161)
