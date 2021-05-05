from yat_api import get_emoji_list, get_infos
from yat_re_results import *

emojis = get_emoji_list()

def emoji_score():
    print("Calulating emojis' score")
    # instead of 5 repeating could put static 4 emos (i'll do it later to check the results)
    res = {}
    for i, e in enumerate(emojis):
        print(i+1, '/', len(emojis), sep='')
        res[e] = get_infos(e*4).get('rhythm_score')
    print(res)

def rs_res_analyze():
    sorted_dict = {}
    emos = sorted(repeat_5_rs, key=repeat_5_rs.get)
    emos.reverse()
    for e in emos:
        sorted_dict[e] = repeat_5_rs[e]
    print(sorted_dict)

def pattern_score():
    pass

def length_score():
    pass

def coming_soon():
    res = []
    for i, e in enumerate(emojis):
        print(i+1, '/', len(emojis), sep='')
        if get_infos(e+'📐📓💼🎋').get('res').get('availability') == 'ComingSoon':
            res.append(e)
    print(res)

if __name__ == "__main__":
    print(get_infos('🥚🐣🦆🍗'))
    #coming_soon()
