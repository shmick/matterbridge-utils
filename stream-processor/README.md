This should be part of your docker compose file

```yaml
version: '3.7'
services:
  matterbridge:
    <config details>
    
  stream-processor:
    build:
      context: ./stream-processor  # Directory containing your Python service
      dockerfile: Dockerfile
    environment:
      - MATTERBRIDGE_HOST=matterbridge
      - MATTERBRIDGE_PORT=4242
      - IMAGE_CACHE_URL=http://img-cache:6161
    depends_on:
      - matterbridge
      - img-cache
    restart: unless-stopped
