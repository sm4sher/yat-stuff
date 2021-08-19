from yat_api import get_emoji_list, YatAPI

import regex
from itertools import product
import logging
import asyncio
import sys

emojis = get_emoji_list()    


def check_id(seq):
    if not 1 <= len(seq) <= 5:
        return False
    for emo in seq:
        if emo not in emojis:
            return False
    return True

def get_yats_from_pattern(pattern):
    logging.info("performing a search for pattern {}".format(pattern))
    q = []
    ids = []
    parse_pattern(pattern, q, ids)
    while q:
        p = q.pop()
        parse_pattern(p, q, ids)
    logging.debug(len(ids))
    if len(ids) > 5000:
        return "Sorry, your pattern is too large ({} possible yats). Please change your pattern and try again".format(len(ids))
    logging.debug(ids)
    return ids

def parse_pattern(pattern, q, ids):
    logging.debug('parsing pattern' + pattern)
    in_brackets = False
    bracket_start = None
    brackets_ended = False
    neg_flag = False
    brackets_set = set()
    ready = True
    pattern = regex.findall(r'\X', pattern, regex.U)
    for i, c in enumerate(pattern):
        logging.debug('  parsing ' + str(c) + ' bracket_set: ' + str(brackets_set))
        if brackets_ended or (c == ']' and i == len(pattern)-1):
            # look for repeater then process
            try:
                rpt = int(c)
                cont = False
            except:
                rpt = 1
                if c != ']':
                    cont = True
                else:
                    cont = False
            s = ''.join(pattern[:bracket_start] + ["{}"]*rpt + pattern[i+(0 if cont else 1):])
            q += [s.format(*emos) for emos in product(brackets_set, repeat=rpt)]
            brackets_set = set()
            in_brackets=False
            brackets_ended = False
            if not cont:
                continue
    
        if c == '.' and not in_brackets:
            ready = False
            s = ''.join(pattern[:i] + ["{}"] + pattern[i+1:])
            q += [s.format(e) for e in emojis]
        elif c == '[':
            ready = False
            in_brackets = True
            bracket_start = i
        elif c == ']':
            ready = False
            in_brackets = False
            neg_flag = False
            brackets_ended = True
        elif in_brackets and c == '^':
            ready = False
            neg_flag=True
        elif in_brackets and c in emojis and neg_flag:
            ready = False
            brackets_set.discard(c)
        elif in_brackets and c in emojis:
            ready = False
            brackets_set.add(c)
        elif in_brackets and c == '*':
            ready = False
            brackets_set.update(emojis)
    if ready and check_id(pattern):
        ids.append(''.join(pattern))
        
async def scan(ids):
    logging.info("checking availability of {} yats".format(len(ids)))
    avails = []
    yat_api = YatAPI()
    res_all = await yat_api.get_infos_bulk(ids)
    for i, res in enumerate(res_all):
        infos = res.get('result')
        # if we didn't get the infos for an emoji_id try again once
        if not infos:
            infos = await yat_api.get_infos(res.get('emoji_id'))
        # if we still don't have it, skip
        if not infos:
            logging.info('pattern scan: Skipping ' + res.get('emoji_id'))
            continue
        avail = infos.get('availability')
        if avail != 'Taken':
            avails.append({
                'id': infos.get('emoji_id'), 
                'rs': infos.get('rhythm_score'), 
                'availability': avail,
                'price': infos.get('price', 0)/100,
                'disc_price': infos.get('discounted_price', 0)/100,
            })
    await yat_api.close()
    return format_results(avails)
            
def format_results(res):
    if len(res) > 0:
        s = "{} Yats matching this pattern are still available:\n".format(len(res))
    else:
        s = "All {} Yats matching this pattern are taken...".format(len(res))
    for e in sorted(res, key=lambda e: e.get('rs'), reverse=True):
        s += "{}\tRS{}\t{}\n".format(
            e.get('id'), e.get('rs'), e.get('availability'))
    return s

if __name__ == "__main__":
    if len(sys.argv) < 2:
        pattern = '🔥.🔥'
    else:
        pattern = sys.argv[1]
    yats = get_yats_from_pattern(pattern)
    result = asyncio.run(scan(yats))
    print(result)
