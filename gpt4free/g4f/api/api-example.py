import requests
import json

url = "http://localhost:6471"

data = {
    "model": "gpt-3.5-turbo",
    "stream": False,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Translate the following English text to French: 'Hello.'"
        }
    ]
}

data_json = json.dumps(data)

headers = {"Content-Type": "application/json"}

response = requests.post(url, data=data_json, headers=headers)

if response.status_code == 200:
    print(response.json()) 
else:
    print("Request failed with status code:", response.status_code)