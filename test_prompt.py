"""
Simple interactive script to test your AI Gateway proxy.
Run with: python test_prompt.py
"""

import urllib.request
import json
import time

def test_gateway():
    url = "http://localhost:8000/v1/chat/completions"
    
    # Prompt containing sensitive PII (Email, Phone, Card)
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": "Contact me at sarah.connor@cyberdyne.org, phone +1-555-234-5678, or bill card 4532 0151 1283 0366."
            }
        ]
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    print("==================================================")
    print(" >>> Sending request to AI Gateway Proxy...")
    print("==================================================")
    
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req) as response:
            latency_ms = (time.perf_counter() - start) * 1000.0
            headers = {k.lower(): v for k, v in response.headers.items()}
            body = json.loads(response.read().decode("utf-8"))
            
            print(f"Status Code:       {response.status} OK")
            print(f"X-Cache:           {headers.get('x-cache')}")
            print(f"X-PII-Redacted:    {headers.get('x-pii-redacted')}")
            print(f"Response Time:     {latency_ms:.2f} ms")
            print("--------------------------------------------------")
            print("Response Content:")
            print(body["choices"][0]["message"]["content"])
            print("--------------------------------------------------")
            print(f"Tokens Used:       {body['usage']['total_tokens']}")
            print("==================================================")
    except urllib.error.URLError as e:
        print(f"[ERROR] Could not connect to Gateway: {e}")
        print("Make sure the server is running on http://localhost:8000")

if __name__ == "__main__":
    test_gateway()
