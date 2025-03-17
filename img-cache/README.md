Add to docker-compose.yml

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
