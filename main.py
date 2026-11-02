import sys
import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

# Ensure UTF-8 output in Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY not found in environment. Please set it in .env")

client = SarvamAI(api_subscription_key=api_key)

response = client.chat.completions(
    model="sarvam-105b-conversations",
    messages=[
        {"role": "user", "content": "Hello! Say hi in Hindi."}
    ],
)

print(response.choices[0].message.content)
