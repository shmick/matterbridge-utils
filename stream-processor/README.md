## stream-processor

A lightweight bridge application that intercepts Discord image URLs from Matterbridge and replaces them with cached versions. This ensures Discord images remain accessible even after they expire from Discord's CDN.

Instead of having a nasty url like: `https://cdn.discordapp.com/attachments/13509801518808586/13512740474255923/foo.png?ex=
67d9c78b&is=67d8760b&hm=c782971ee291c0301f751aecdec829f8bdc797ea0d4b65565143f86bc2915722&` sent to IRC, you get a nice url like `https://imgs.example.com/i/e80842b8.png`


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
