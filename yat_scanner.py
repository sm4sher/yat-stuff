
from yat_api import is_emoji_out, test, get_emoji_list
import config

from discord.ext import tasks
from discord import NotFound

from datetime import datetime
import logging

class YatScanner:
    COMING_SOON = ['🧠', '✨', '🤯', '♿', '🥶']

    
    def __init__(self, bot):
        self.bot = bot
        self.last_scan = None
        self.sent_notifs = []
        self.initial_list = get_emoji_list()
    
    def is_running(self):
        return self.task_scanner.is_running()
    
    def start(self):
        if not self.initial_list:
            logging.warning("Scanner initial list wasn't initialized correctly. Not starting task")
        elif True in scan():
            logging.warning("One of the ComingSoon emoji is available! Are you sure that's not a mistake? Not starting task")
        else:
            logging.info('Starting scanner task')
            self.task_scanner.start()
    
    @tasks.loop(seconds=15)
    async def task_scanner(self):
        # first let's see if any new emojis were added to the emojis endpoint (if they're just ComingSoon we don't really care but could still be interesting)
        newlist = await self.bot.loop.run_in_executor(None, get_emoji_list)
        if newlist and len(newlist) > len(self.initial_list):
            new_emos = set(newlist) - set(self.initial_list)
            await self.alert("[ALERT] New emoji might be coming soon: " + ', '.join(new_emos))
            self.initial_list = newlist

        # for each emoji in the ComingSoon list, see if it changed
        res = await self.bot.loop.run_in_executor(None, scan)
        for i, r in enumerate(res):
            emo = self.COMING_SOON[i]
            if r and emo not in self.sent_notifs:
                logging.warning('EMOJI {} IS AVAILABLE!'.format(emo))
                await self.alert('[ALERT] It looks like the emoji {} is now available on Yat! Go check it now'.format(emo))
                self.sent_notifs.append(emo)
        self.last_scan = datetime.now()
    
    async def alert(self, msg):
        for uid in config.NEW_EMOJI_NOTIF:
            try:
                u = await self.bot.fetch_user(uid)
            except NotFound:
                logging.warning('Scanner alert: User not found with id {}'.format(uid)) 
                continue       
            try:     
                await u.send(msg)
            except:
                logging.exception("couldn't send notification to {}".format(u))
                continue

def scan():
    return [is_emoji_out(e) for e in YatScanner.COMING_SOON]
