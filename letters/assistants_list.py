import openai
from django.conf import settings
import requests
import os

API_KEY = "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"


resp = requests.get(
    "https://api.openai.com/v1/assistants",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
        "OpenAI-Beta":   "assistants=v2",    # ← добавили этот заголовок
    }
)

print("status:", resp.status_code)
print(resp.json())