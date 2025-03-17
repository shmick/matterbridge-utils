import json
import re
import requests
import os
import time
from queue import Queue
from threading import Thread
from urllib3.poolmanager import PoolManager

# Environment variables with defaults
MATTERBRIDGE_HOST = os.getenv('MATTERBRIDGE_HOST', 'matterbridge')
MATTERBRIDGE_PORT = os.getenv('MATTERBRIDGE_PORT', '4242')
IMAGE_CACHE_URL = os.getenv('IMAGE_CACHE_URL', 'http://img-cache:6161')
DEBUG = os.getenv('DEBUG') is not None

# Construct Matterbridge API URLs
MATTERBRIDGE_BASE_URL = f'http://{MATTERBRIDGE_HOST}:{MATTERBRIDGE_PORT}'
MATTERBRIDGE_STREAM_URL = f'{MATTERBRIDGE_BASE_URL}/api/stream'
MATTERBRIDGE_MESSAGE_URL = f'{MATTERBRIDGE_BASE_URL}/api/message'

# Optimized regex pattern
DISCORD_URL_PATTERN = re.compile(r'https?://(?:cdn\.discordapp\.com|media\.discordapp\.net)/(?:attachments|external)/[^\s]+')

# Gateway mapping dictionary
GATEWAY_MAPPINGS = {
    'fin2-disc': 'fin2-api',
    'fin2-api': 'fin2-irc',
    'fin2-irc': 'fin2-disc'
}

# Create connection pool
http = PoolManager(maxsize=10)
message_queue = Queue(maxsize=1000)

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def process_url(message: str, url: str) -> str:
    debug_print(f"Processing URL: {url}")
    try:
        response = http.request(
            'POST',
            f'{IMAGE_CACHE_URL}/cache',
            json={'message': message, 'url': url}
        )
        if response.status == 200:
            modified = json.loads(response.data.decode('utf-8'))['modified_message']
            debug_print(f"Modified message: {modified}")
            return modified
    except Exception as e:
        debug_print(f"Error calling image cache API: {e}")
    return message

def process_message(message_text: str) -> str:
    debug_print(f"Processing message: {message_text}")
    if not message_text:
        return message_text
        
    modified_text = message_text
    urls = list(DISCORD_URL_PATTERN.finditer(message_text))
    
    if urls:
        debug_print("Found Discord URL in message")
        for url_match in urls:
            discord_url = url_match.group(0)
            modified_text = process_url(modified_text, discord_url)
    else:
        debug_print("No Discord URLs found in message")
    
    return modified_text.replace('\n', ' ').strip()

def parse_line(line: str) -> dict:
    try:
        if line.startswith('data:'):
            data = line[5:].strip()
        else:
            data = line.strip()
            
        if data:
            return json.loads(data)
    except json.JSONDecodeError as e:
        debug_print(f"Error parsing JSON: {e}")
    return None

def process_message_queue():
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=100)
    session.mount('http://', adapter)
    
    while True:
        try:
            msg = message_queue.get()
            if msg is None:
                break
                
            if msg.get('text'):
                processed_text = process_message(msg['text'])
                response = session.post(
                    MATTERBRIDGE_MESSAGE_URL,
                    json={
                        'text': processed_text,
                        'username': msg.get('username', 'unknown'),
                        'gateway': msg['api_gateway']
                    },
                    timeout=5
                )
                debug_print(f"Message sent, status: {response.status_code}")
                if response.status_code != 200:
                    debug_print(f"Error sending message, status code: {response.status_code}")
                    
            message_queue.task_done()
            
        except Exception as e:
            debug_print(f"Error in message queue processing: {e}")
            continue

def main():
    debug_print("Starting message processing...")
    debug_print(f"Matterbridge URL: {MATTERBRIDGE_BASE_URL}")
    debug_print(f"Image Cache URL: {IMAGE_CACHE_URL}")
    debug_print(f"Debug mode: {DEBUG}")
    
    processor = Thread(target=process_message_queue, daemon=True)
    processor.start()
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=100)
    session.mount('http://', adapter)
    
    reconnect_delay = 1
    max_reconnect_delay = 30
    
    while True:
        try:
            debug_print("Connecting to Matterbridge stream...")
            response = session.get(
                MATTERBRIDGE_STREAM_URL,
                stream=True,
                timeout=(3.05, None)
            )
            response.encoding = 'utf-8'
            debug_print(f"Connected to stream with status: {response.status_code}")
            
            # Reset reconnect delay on successful connection
            reconnect_delay = 1
            
            for line in response.iter_lines(decode_unicode=True):
                if not line or line == "":
                    continue
                
                debug_print("----------------------------------------")
                debug_print(f"Raw line received: {line}")
                
                msg = parse_line(line)
                if not msg:
                    continue
                
                if DEBUG:
                    debug_print(f"Parsed message details:")
                    debug_print(f"  Gateway: {msg.get('gateway')}")
                    debug_print(f"  Username: {msg.get('username')}")
                    debug_print(f"  Text: {msg.get('text')}")
                
                if msg.get('event') == 'api_connected':
                    debug_print("API Connected successfully")
                    continue
                
                api_gateway = GATEWAY_MAPPINGS.get(msg.get('gateway'))
                if api_gateway:
                    msg['api_gateway'] = api_gateway
                    message_queue.put(msg)
                
        except Exception as e:
            debug_print(f"Stream error: {e}")
            try:
                response.close()
            except:
                pass
            
            debug_print(f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
            continue

if __name__ == '__main__':
    main()
