import os 
import requests
import json
import pandas as pd
from time import perf_counter
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
claude_api_key = os.environ.get('ANTHROPIC_API_KEY')

if not claude_api_key:
    raise ValueError('The ANTHROPIC_API_KEY is not set or invalid ... !')

url = 'https://api.anthropic.com/v1/messages'

headers = {'x-api-key' : claude_api_key,
        'anthropic-version' : '2023-06-01'
        }

body = {
        "model":"claude-haiku-4-5-20251001",
        "max_tokens":150,
        "messages":[{
            "role" : "user",
            "content":"Hello, How are you doing today? this is me mosab speaking"
            }]
        }
response = requests.post(url=url, headers=headers, json=body)

data = response.json()

print(response.status_code)
print(data)