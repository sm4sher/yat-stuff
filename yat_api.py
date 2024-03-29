import requests
import aiohttp
import asyncio
from multiprocessing import Pool
import config

import logging
import random
import time

API_URL = "https://a.y.at"

def get_auth_headers():
    h = {'Accept': '*/*'}
    if config.YAT_API_KEY:
        h['Authorization'] = config.YAT_API_KEY
        h['X-Api-Key'] = config.YAT_API_KEY
    else:
        h['Authorization'] = 'Bearer {}'.format(config.YAT_TOKEN)
    return h

def create_api_key(name):
    path = API_URL + '/api_keys'
    data = {'name': name}
    r = requests.post(path, json=data, headers=get_auth_headers())
    print(r.text)
    if r.status_code == 200:
        return r.json()
    return False

def test_endpoint(path):
    path = API_URL + path
    r = requests.get(path, headers=get_auth_headers())
    if r.status_code != 200:
        print("Status:", r.status_code)
        print(r.text)
    else:
        print(r.json())

def test_proxy():
    path = API_URL + '/proxy'
    data = {'service': 'Scraper', 'data': 'https://google.com'}
    r = requests.post(path, headers=get_auth_headers(), json=data)
    if r.status_code != 200:
        print("Status:", r.status_code)
        print(r.text)
    else:
        print(r.json())

def get_emoji_list():
    path = API_URL + '/emoji'
    r = requests.get(path, headers={'Accept': '*/*'})
    if r.status_code == 200:
        return r.json()
    return False

def get_infos(emoji_id):
    path = API_URL + '/emoji_id/search?emoji_id={}'.format(emoji_id)
    r = requests.get(path, headers={'Accept': '*/*'})
    if r.status_code == 200:
        return {'id': emoji_id, 'res': r.json().get('result')}
    return {'id': emoji_id, 'res': False}

def get_data(emoji_id):
    path = API_URL + '/emoji_id/{}'.format(emoji_id)
    r = requests.get(path, headers={'Accept': '*/*'})
    if r.status_code == 200:
        return r.json().get('result')
    return False

def fast_get_infos(ids):
    if not ids:
        return []
    with Pool(min(10, len(ids)//2)) as p:
        return p.map(get_infos, ids)

def is_emoji_out(emoji):
    random_emojis = [
        '📐', '📓', '💼', '🎋', '🤢', '🤓', '🍎', '🍵', '🦆', '💡', '💈', '👶', '🎮', '🚢', '😘', '⚖️',
        '🏒', '🚲', '🛢️', '👙', '☪️', '🚿', '🥜', '🌪️', '💦', '🤕'
    ]
    yat = "{}{}{}{emo}{}".format(*[random.choice(random_emojis) for _ in range(4)], emo=emoji)
    res = get_infos(yat)
    infos = res.get('res')
    if not infos:
        logging.warning("Scan didn't work for yat {} with emoji {}.".format(res.get('id'), emoji))
        return False
    available = infos.get('availability')
    if available is None:
        logging.warning("Infos didn't have availability field. Did it change? get_infos returned:\n{}".format(res))
        return False
    if available != 'ComingSoon':
        # WOW!
        return True
    return False

def get_recent_purchases():
    path = API_URL + '/emoji_id/recent'
    r = requests.get(path, headers={'Accept': '*/*'}, timeout=5)
    if r.status_code != 200:
        return False
    return r.json().get('result')

class YatAPI:
    API_URL = "https://a.y.at"

    def __init__(self):
        self.aiosession = None

    async def get_metadata(self, token_id):
        s = await self.get_aiosession()
        path = self.API_URL + '/nft_transfers/metadata/{}'.format(token_id)
        async with s.get(path) as r:
            if r.status != 200:
                return False
            return await r.json()
    
    async def get_infos(self, emoji_id):
        s = await self.get_aiosession()
        path = self.API_URL + '/emoji_id/search'
        params = {'emoji_id': emoji_id}
        async with s.get(path, params=params) as r:
            if r.status != 200:
                return False
            resp_json = await r.json()
            return resp_json.get('result')

    async def get_infos_bulk(self, emoji_ids):
        emoji_ids = tuple(emoji_ids) # support receiving sets
        tasks = (self.get_infos(emoji_id) for emoji_id in emoji_ids)
        res = await asyncio.gather(*tasks, return_exceptions=True)
        ret = []
        for i, infos in enumerate(res):
            if not infos or isinstance(infos, Exception):
                ret.append({'emoji_id': emoji_ids[i], 'result': False})
            else:
                ret.append({'emoji_id': emoji_ids[i], 'result': infos})
        return ret

    async def get_recent_purchases(self):
        s = await self.get_aiosession()
        path = self.API_URL + '/emoji_id/recent'
        async with s.get(path) as r:
            if r.status != 200:
                return False
            resp_json = await r.json()
            return resp_json.get('result')

    # consider making a helper parent class for this and OpenseaFeeder
    async def get_aiosession(self):
        if self.aiosession is not None:
            return self.aiosession
        self.aiosession = aiohttp.ClientSession()
        return self.aiosession

    async def close(self):
        if self.aiosession is not None:
            await self.aiosession.close()


def paste(s):
    '''post s to pastebin and returns the link (yes this has nothing to do here)'''
    logging.info('posting to pastebin')
    url = "https://pastebin.com/api/api_post.php"
    data = {
        'api_dev_key': config.PASTEBIN_API_KEY,
        'api_option': "paste",
        'api_paste_code': s,
        'api_paste_private': '1'
    }
    r = requests.post(url, data=data)
    logging.info('paste result: {}'.format(r.text))
    return r.text
    
if __name__ == "__main__":
    print(get_info('🔥🔥🔥'))
