import requests

response = requests.get('http://127.0.0.1:8443/health')
print(response.status_code)
print(response.text)

