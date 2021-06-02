import logging
import sqlite3
import asyncio
import os
from datetime import datetime, timezone, timedelta

import discord

from yat_api import get_recent_purchases

class YatFeeder:
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('feed.db')
        self.init_db()
        self.load_config()

    def db_exec(self, q, args=(), many=False):
        cur = self.db.cursor()
        if many:
            cur.executemany(q, args)
        else:
            cur.execute(q, args)
        self.db.commit()
        return cur

    def init_db(self):
        self.db = sqlite3.connect('feed.db')
        # snwoflake ids should be int? if sqlite supports 64bits int
        self.db_exec("CREATE TABLE IF NOT EXISTS purch_yats (date text, yat text, rs int)")
        self.db_exec("CREATE TABLE IF NOT EXISTS livefeeds (created_date text, channel_id text, creator_id text, enabled int)")
        self.db_exec("CREATE TABLE IF NOT EXISTS announcements (id INTEGER PRIMARY KEY, filename text, sched_date text, sent int)")

    def load_config(self):
        cur = self.db_exec("SELECT channel_id FROM livefeeds WHERE enabled=1")
        lines = cur.fetchall()
        self.channels = set()
        for line in lines:
            chan = self.bot.get_channel(int(line[0]))
            if chan is None:
                self.db_exec("UPDATE livefeeds SET enabled=0 WHERE channel_id=?", (line[0],))
            else:
                self.channels.add(chan)

        cur = self.db_exec("SELECT yat FROM purch_yats")
        self.processed_list = {line[0] for line in cur.fetchall()}

    def update_processed_list(self, yats):
        self.processed_list |= {y.get('emoji_id') for y in yats}
        values = [((datetime.now(tz=timezone.utc)-timedelta(hours=22)).isoformat(), y.get('emoji_id'), y.get('rhythm_score')) for y in yats]
        self.db_exec("INSERT INTO purch_yats (date, yat, rs) VALUES (?, ?, ?)", values, many=True)

    def register_chan(self, channel, creator):
        self.channels.add(channel)
        self.db_exec("INSERT INTO livefeeds (created_date, channel_id, creator_id, enabled) VALUES (?, ?, ?, 1)",
            (datetime.now().isoformat(), channel.id, creator.id))

    def unregister_chan(self, channel):
        try:
            self.channels.remove(channel)
        except KeyError:
            return False, "No active livefeed in this channel"
        self.db_exec("UPDATE livefeeds SET enabled=0 WHERE channel_id=?", (channel.id,))
        return True, ''

    async def send(self, msg):
        tasks = [chan.send(msg) for chan in self.channels]
        # if channel has been deleted it will return discord.NotFound exception. We will disable it at next bot restart
        await asyncio.gather(*tasks, return_exceptions=True)

    async def check_annoucements(self):
        announcements = self.db_exec("SELECT id, filename FROM announcements WHERE sent=0 AND datetime('now') >= datetime(sched_date)").fetchall()
        for ann in announcements:
            await self.make_annoucement({'id': ann[0], 'filename': ann[1]})

    async def make_annoucement(self, ann):
        logging.info('Sending livefeed annoucement id {}'.format(ann['id']))
        with open(os.path.join('announcements', ann['filename']), "r") as f:
            content = f.read()
        self.db_exec("UPDATE announcements SET sent=1 WHERE id=?", (ann['id'],))
        await self.send(content)

    def start(self):
        logging.info('Starting feeder task for {} livefeeds'.format(len(self.channels)))
        self.task_feeder.start()

    @discord.ext.tasks.loop(seconds=30)
    async def task_feeder(self):
        await self.check_annoucements()
        # get list of recently purchased yats
        recent = get_recent_purchases()
        if not recent:
            logging.warning("Couldn't get list of recent yat purchases")
            return
        # filter out those we already processed
        recent.reverse() # api returns them from most recent to least recent
        new = [y for y in recent if y.get('emoji_id') not in self.processed_list]
        if not new:
            return
        self.update_processed_list(new)
        # send msgs in each livefeed
        msg = "\n".join(["{} (RS{})".format(y.get('emoji_id'), y.get('rhythm_score')) for y in new])
        await self.send(msg)

    def get_recent_yats(self, limit=10):
        cur = self.db_exec("SELECT yat, rs FROM purch_yats ORDER BY date DESC LIMIT ?", (limit,))
        return [{'emoji_id': y[0], 'rhythm_score': y[1]} for y in cur]


    