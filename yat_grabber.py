import requests
import config

from base64 import urlsafe_b64decode as b64d
from binascii import Error as B64Error
import json
import time

API_URL = "https://a.y.at"

def check_token():
    token = config.YAT_TOKEN
    plb64 = token.split('.')[1]
    while True:
        try:
            pl = json.loads(b64d(plb64).decode())
            break
        except B64Error:
            plb64 += '='
        if '====' in plb64:
            print('YAT_TOKEN error')
            return False
    remaining_sec = pl.get('exp') - time.time()
    if remaining_sec < 30:
        print('yat token expired')
        return False
    print("yat token expiring in {} seconds".format(remaining_sec))
    return True

def add_to_cart():
    if not check_token():
        return
    headers = {
        'Host': 'a.y.at', # no idea if we actually need to add it or not...
        'Accept': 'application/json',
        'Accept-Enconding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'content-type': 'application/json',
        'Referer': 'https://y.at/create',
        'Origin': 'https://y.at',
        'Authorization': 'Bearer {}'.format(config.YAT_TOKEN),
        'DNT': '1',
        'Pragma': 'no-cache',
        'Cache-control': 'no-cache',
        'TE': 'Trailers',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    s = requests.Session()
    data = {"items": [
        {'emoji_id': '🤯🤯🤯'},
        #{'emoji_id': '✨✨✨✨'}
    ]}
    r = s.post(API_URL+'/cart', headers=headers, timeout=5, json=data)
    print(r.text)
    if r.status_code != 200:
        print("Adding items to cart didn't work!")
        return False
    cart_id = r.json().get('id')
    # make 2 get req to look normal :p
    r = s.get(API_URL+'/cart', headers=headers, timeout=5, json=data)
    headers['Referer'] = 'https://y.at/checkout'
    r = s.get(API_URL+'/cart', headers=headers, timeout=5, json=data)
    print(r.text)

    # checkout! (bruh I forgot to finish this that's why it didn't work -_- TODO!)
    r = s.post(API_URL+'/')
    return True

if __name__ == "__main__":
    while True:
        if add_to_cart():
            break
        #time.sleep(0.5)