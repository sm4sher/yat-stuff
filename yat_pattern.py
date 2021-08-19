from yat_api import get_emoji_list, YatAPI
from yat_utils import split_yat

import regex
from itertools import product
import logging
import asyncio
import sys
import string

emojis = get_emoji_list()    

class PatternException(Exception):
    pass

def check_id(seq):
    if not 1 <= len(seq) <= 5:
        return False
    for emo in seq:
        if emo not in emojis:
            return False
    return True

def get_yats_from_pattern(pattern):
    logging.info("performing a search for pattern {}".format(pattern))
    if len(split_yat(pattern)) > 10:
        raise PatternException("Your pattern is too long")
    q = set()
    ids = set()
    parse_pattern(pattern, q, ids)
    while q:
        p = q.pop()
        parse_pattern(p, q, ids)
    logging.debug(len(ids))
    logging.debug(ids)
    return ids

# v2: simpler, betterer
# A, B, C, D, E = any emoji, same letter = same emoji
# Af -> only faces, Ao -> objects, Afo -> face & objects ....

FACE_EMOJIS = ['😂', '😇', '🙃', '😍', '😜', '😘', '🤓', '😎', '😢', '🤯', '😱', '🤔', '😶', '😵', '🤐', '🤢', '🤧', '😷', '🤕', '🤑', '🤠', '😈', '🤡', '💩', '👻', '☠️', '👽', '👾', '🤖', '🎃', '👶', '🐶', '🐱', '🐭', '🐰', '🦊', '🐻', '🐼', '🐮', '🐨', '🐯', '🦁', '🐷', '🐸', '🐵', '🙈', '🐔', '🐧', '🐣', '🦆', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🥺', '😏']
HUMAN_EMOJIS = []
ANIMAL_EMOJIS = []
# most popular bookends as of august 2021 (excluding 👂 which doesn't really make sense out of face yats )
BOOKEND_EMOJIS = ['⭐', '✨', '⚡', '🔥', '❤️', '☁️', '♾️', '💎', '👑', '🌊', '🌈', '⛓️', '🛡️'] # ......
CLOTHES_EMOJIS = []
SYMBOLS_EMOJIS = []


def get_emojis(mods=None):
    if not mods:
        return emojis
    s = set()
    for m in mods:
        if m == 'f': # face
            s.update(FACE_EMOJIS)
        elif m == 'b': # bookends
            s.update(BOOKEND_EMOJIS)
        else:
            raise PatternException("Unrecognized modifier: '{}'".format(m))
    return s

def parse_pattern(pattern, q, ids):
    logging.debug("parsing pattern" + pattern)
    # split pattern in chars
    pattern = split_yat(pattern)
    # check if we have a valid yat
    if check_id(pattern):
        ids.add(''.join(pattern))
        return
    # we still have things to parse
    q_complexity = 0
    i = 0
    while i < len(pattern):
        logging.debug("queue: {}, queue complexity: {}, valid ids: {}".format(len(q), q_complexity, len(ids)))
        if len(q) > 5000 or len(ids) > 5000 or q_complexity > 50:
            raise PatternException("Sorry, your pattern is too complex. Please change your pattern and try again")
        c = pattern[i]
        if c in string.ascii_uppercase:
            logging.debug("found var {}".format(c))
            mods = []
            for j in range(i+1, len(pattern)):
                if pattern[j] in string.ascii_lowercase:
                    mods.append(pattern[j])
                else:
                    break
            logging.debug("  mods: {}".format(mods))
            # replace all occurence of the variable (and it's mods if any) with "[REP]"
            pattern_rep = regex.sub(r"{}[a-z]*".format(c), "[REP]", ''.join(pattern))
            sub_emojis = get_emojis(mods)
            # add new patterns with substituted vars to the queue
            q.update([pattern_rep.replace("[REP]", e) for e in sub_emojis])
            # remake the split pattern without the var we just handled
            pattern_rep = pattern_rep.replace("[REP]", "_")
            pattern = split_yat(pattern_rep)
            # avoid getting in too deep by determining the complexity added to the queue
            # i'm too tired to do it properly, should be enough to prevent at least accidental dos
            q_complexity += len(sub_emojis) * len(set(regex.findall('[A-Z]', pattern_rep)))
        elif c not in emojis and c != '_':
            raise PatternException("Unrecognized character or emoji: '{}'".format(c))
        i += 1
        
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
        s = "All Yats matching this pattern are taken..."
    for e in sorted(res, key=lambda e: e.get('rs'), reverse=True):
        s += "{}\tRS{}\t{}\n".format(
            e.get('id'), e.get('rs'), e.get('availability'))
    return s

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 2:
        pattern = 'Ab😎A'
    else:
        pattern = sys.argv[1]
    yats = get_yats_from_pattern(pattern)
    input("Scan {} yats?".format(len(yats)))
    result = asyncio.run(scan(yats))
    print(result)
