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
        f.write('date,eid,rs,length\n')
        for y in yats:
            f.write('{},{},{},{}\n'.format(y['date'], y['emoji_id'], y['rs'], len(split_yat(y['emoji_id']))))

def create_rs_chart(yats):
    fig, ax = plt.subplots()
    plot_rs_for_length(ax, yats, 3, color='red')
    plot_rs_for_length(ax, yats, 4, color='blue')
    plot_rs_for_length(ax, yats, 5, color='green')
    plt.show()

def plot_rs_for_length(ax, yats, n, color=None):
    yats = [yat for yat in yats if len(split_yat(yat['emoji_id'])) == n]
    x = [yat['date'] for yat in yats]
    y = [yat['rs'] for yat in yats]
    ax.plot_date(x, y, xdate=True, ms=2, mec=color, mfc=color, label='{}x yats'.format(n))
    ax.legend()

def print_top_by_rs(yats, n=10):
    top = sorted(yats, key=lambda y: y['rs'], reverse=True)[:n]
    for i, yat in enumerate(top):
        print('{}: {} (RS{})'.format(i+1, yat['emoji_id'], yat['rs']))

def time_chart(yats, hourly=False):
    start = datetime(year=2021, month=5, day=13)
    end = datetime(year=2021, month=5, day=31, hour=23)
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
    plt.show()


if __name__ == "__main__":
    start = date(2021, 5, 31)
    end = date(2021, 5, 31)
    yats = load_yats(start, end)
    total_cnt = len(yats)
    cnt_3 = get_count_by_length(yats, 3)
    cnt_4 = get_count_by_length(yats, 4)
    cnt_5 = get_count_by_length(yats, 5)
    avg_rs = round(sum([y['rs'] for y in yats])/len(yats), 2)
    cnt_rs_90 = len([True for y in yats if y['rs'] >= 90])
    print('Between {} and {}, {} yats have been purchased!'.format(start, end, total_cnt))
    print('{} were 3 emojis, {} were 4 emojis and {} were 5 emojis.'.format(cnt_3, cnt_4, cnt_5))
    print('Average Rythm Score was {}, with {} yats above RS90'.format(avg_rs, cnt_rs_90))
    emojis = split_yats(yats)
    print("\n==== Emojis Leaderboard ====\n")
    print_top(emojis)
    print("\n==== RS Leaderboard ====\n")
    print_top_by_rs(yats)


    #export_csv(yats)
    #create_rs_chart(yats)
    time_chart(yats)
