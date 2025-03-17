# Matterbridge stream processor

A Python application that works with Matterbridge to relay messages between different chat platforms, with special handling for Discord image attachments.

## Overview

This application serves as a message processor and relay system that:
- Connects to a Matterbridge instance to handle cross-platform chat communication
- Processes Discord image URLs through an image cache service
- Maintains persistent connections with automatic reconnection
- Supports message queuing for reliable delivery

## Features

- **Discord Image Processing**: Automatically detects and processes Discord CDN URLs (attachments and external media)
- **Message Queue System**: Implements a threaded queue for reliable message processing
- **Automatic Reconnection**: Implements exponential backoff for connection retries
- **Gateway Mapping**: Supports message routing between different platforms (Discord, IRC, API)
- **Debug Mode**: Detailed logging when DEBUG environment variable is set

## Why

Instead of having a nasty url like: `https://cdn.discordapp.com/attachments/13509801518808586/13512740474255923/foo.png?ex=
67d9c78b&is=67d8760b&hm=c782971ee291c0301f751aecdec829f8bdc797ea0d4b65565143f86bc2915722&` sent to IRC, you get a nice url like `https://imgs.example.com/i/e80842b8.png`


## Add to docker-compose.yml

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
