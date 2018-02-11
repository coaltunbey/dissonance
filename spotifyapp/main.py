import requests


url = 'https://accounts.spotify.com/authorize/?client_id=2b560bec6aba43e6aa97072392c57077&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fcallback&scope=user-library-read'

response = requests.get(url)

print(response.content)

