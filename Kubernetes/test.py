import requests

session = requests.Session()
response = session.get('http://tamer.atech-bot.click/results?predictionId=test', allow_redirects=True, verify=False)

print(f"Status Code: {response.status_code}")
print(f"Final URL: {response.url}")
print(f"Response Text: {response.text}")
