import requests
from multiprocessing import Pool
import config

import logging
import random
import time

API_URL = "https://a.y.at"

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

def test(emoji):
    print('running')
    return False
    

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
