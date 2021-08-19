import sqlite3
import regex
from collections import Counter
from datetime import datetime, date, timedelta

import matplotlib.pyplot as plt

from yat_utils import split_yat

def load_yats(start, end):
    db = sqlite3.connect('feed.db')
    cur = db.cursor()
    cur.execute("SELECT date, yat, rs FROM purch_yats WHERE date(date) BETWEEN ? AND ?", (start.isoformat(), end.isoformat()))
    return [{'date': datetime.fromisoformat(y[0]), 'emoji_id': y[1], 'rs': y[2]} for y in cur.fetchall()]

def split_yats(yats):
    emojis = []
    for y in yats:
        emojis += split_yat(y['emoji_id'])
    return emojis

def print_top(t, n=10):
    top = Counter(t).most_common(n)
    for i, e in enumerate(top):
        print('{}: {} ({})'.format(i+1, e[0], e[1]))

def get_count_by_length(yats, n):
    return len([True for y in yats if len(split_yat(y['emoji_id'])) == n])

def export_csv(yats):
    with open('stats.csv', 'w+') as f:
        f.write('date,yat,rs,length\n')
        for y in yats:
            f.write('{},{},{},{}\n'.format(y['date'], '-'.join(split_yat(y['emoji_id'])), y['rs'], len(split_yat(y['emoji_id']))))

def create_rs_chart(yats):
    fig, ax = plt.subplots()
    plot_rs_for_length(ax, yats, 3, color='red')
    plot_rs_for_length(ax, yats, 4, color='blue')
    plot_rs_for_length(ax, yats, 5, color='green')
    fig.autofmt_xdate()
    fig.legend(loc='center right')
    fig.suptitle('RS of created Yats of different lengths over time')
    plt.show()

def plot_rs_for_length(ax, yats, n, color=None):
    yats = [yat for yat in yats if len(split_yat(yat['emoji_id'])) == n]
    x = [yat['date'] for yat in yats]
    y = [yat['rs'] for yat in yats]
    ax.plot_date(x, y, xdate=True, ms=2, mec=color, mfc=color, label='{}x yats'.format(n))

def print_top_by_rs(yats, n=10):
    top = sorted(yats, key=lambda y: y['rs'], reverse=True)[:n]
    for i, yat in enumerate(top):
        print('{}: {} (RS{})'.format(i+1, yat['emoji_id'], yat['rs']))

def time_chart(yats, start, end, hourly=False):
    start = datetime(year=start.year, month=start.month, day=start.day)
    end = datetime(year=end.year, month=end.month, day=end.day, hour=23)
    x = []
    while start <= end:
        x.append(start)
        if hourly:
            start += timedelta(hours=1)
        else:
            start += timedelta(days=1)
    y = [
        len([y for y in yats 
            if y['date'].year == p.year 
              and y['date'].month == p.month 
              and y['date'].day == p.day
              and (not hourly or y['date'].hour == p.hour)])
        for p in x]
    fig, ax = plt.subplots()
    ax.bar(x, y, width=1/24 if hourly else 0.95)
    ax.xaxis_date()
    fig.autofmt_xdate()
    fig.suptitle("Number of Yats bought per {}".format('hour' if hourly else 'day'))
    plt.show()

def top_bookends(yats):
    emojis = []
    for y in yats:
        split = split_yat(y['emoji_id'])
        if split[0]==split[-1]:
            emojis.append(split[0])
    print_top(emojis, n=20)

def top_double_bookends(yats, exclude_same=False):
    emojis = []
    for y in yats:
        split = split_yat(y['emoji_id'])
        if len(split) != 5: continue
        if split[0]==split[-1] and split[1]==split[-2] and (not exclude_same or split[0]!=split[1]):
            emojis.append(''.join(split[0:2]))
    print_top(emojis, n=20)

def top_bookended(yats):
    emojis = []
    for y in yats:
        split = split_yat(y['emoji_id'])
        if len(split)==3 and split[0]==split[-1]:
            emojis.append(split[1])
        if len(split)==5 and split[0]==split[-1] and split[1]==split[-2]:
            emojis.append(split[2])
    print_top(emojis, n=20)

def top_adoptable_emojis(yats):
    emojis = []
    for y in yats:
        adopt_score = 0
        if '👖' in y['emoji_id']: adopt_score+=1
        if '👟' in y['emoji_id']: adopt_score+=1
        if '👕' in y['emoji_id']: adopt_score+=1
        if '👞' in y['emoji_id']: adopt_score+=1
        if adopt_score < 2:
            continue
        emojis += split_yat(y['emoji_id'])
    print_top(emojis)

def gen_stats():
    start = date(2021, 5, 12)
    end = date(2021, 8, 31)
    yats = load_yats(start, end)
    total_cnt = len(yats)
    cnt_3 = get_count_by_length(yats, 3)
    cnt_4 = get_count_by_length(yats, 4)
    cnt_5 = get_count_by_length(yats, 5)
    avg_rs = round(sum([y['rs'] for y in yats])/len(yats), 2)
    cnt_rs_90 = len([True for y in yats if y['rs'] >= 90])
    print('Between {} and {}, **{}** yats have been created!'.format(start, end, total_cnt))
    print('**{}** were 3 emojis, **{}** were 4 emojis and **{}** were 5 emojis.'.format(cnt_3, cnt_4, cnt_5))
    print('Average Rhythm Score was **{}**, with **{}** yats above RS90'.format(avg_rs, cnt_rs_90))
    emojis = split_yats(yats)
    print("\n**==== Emojis Leaderboard ====**\n")
    print_top(emojis)
    print("\n**==== RS Leaderboard ====**\n")
    print_top_by_rs(yats)
    create_rs_chart(yats)
    time_chart(yats, start, end)

if __name__ == "__main__":
    #gen_stats()
    #export_csv(yats)
    #exit()
    start = date(2020, 5, 1)
    end = date(2022, 8, 30)
    yats = load_yats(start, end)
    top_bookended(yats)
