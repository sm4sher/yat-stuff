import asyncio
import logging
import aiohttp
import datetime

from yat_twitter import TwitterBot

class OpenseaFeeder:
    REFRESH_INTERVAL = 200
    API_URL = "https://api.opensea.io/api/v1"
    CONTRACT_ADDRESS = "0x7d256d82b32d8003d1ca1a1526ed211e6e0da9e2"
    TWITTER_TEMPLATE = "\"{yatname}\" was just bought for {tokenprice} {tokensymbol} (${usdprice})!\n\n#yat #nft #opensea\n{oslink}"
    DISCORD_TEMPLATE = "\"{yatname}\" was just bought for {tokenprice} {tokensymbol} (${usdprice})!\n\n{oslink}"

    def __init__(self, discord=None):
        self.task = None
        self.aiosession = None

        self.load_last_sales_check()
        self.twitter = TwitterBot()
        self.discord = discord

    def start(self):
        if self.task is not None:
            logging.warning("Couldn't start OpenseaFeeder task: already running")
        logging.info("Starting OpenseaFeeder task")
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.run())

    def stop(self):
        logging.info("Stopping OpenseaFeeder task")
        self.task.cancel()

    async def run(self):
        logging.info("OpenseaFeeder task running")
        while True:
            try:
                await self.check_new_sales()
                await asyncio.sleep(self.REFRESH_INTERVAL)
            except asyncio.CancelledError:
                if self.aiosession is not None:
                    await self.aiosession.close()
                self.task = None
                logging.info("Stopped OpenseaFeeder task")
                break
            except Exception as e:
                logging.exception("Error during OpenseaFeeder operation:")
                await asyncio.sleep(5)

    def fill_template(self, template, s):
        token_price=int(s['total_price']) / (10 ** s['payment_token']['decimals'])
        return template.format(
            oslink=s['asset']['permalink'],
            yatlink=s['asset']['external_link'],
            imglink=s['asset']['image_original_url'],
            vidlink=s['asset']['animation_original_url'],
            yatname=s['asset']['name'],
            yatemojis="", # url decode yat link?
            tokenprice=token_price,
            tokensymbol=s['payment_token']['symbol'],
            usdprice=round(token_price*float(s['payment_token']['usd_price']))
        )

    async def handle_new_sale(self, s):
        # not really async yet but should be at some point (depends on tweepy)
        twitter_txt = self.fill_template(self.TWITTER_TEMPLATE, s)
        await self.twitter.send_tweet(twitter_txt)

        if self.discord is not None:
            discord_txt = self.fill_template(self.DISCORD_TEMPLATE, s)
            self.discord.feeder.send(discord_txt)

    async def check_new_sales(self):
        sales = await self.get_events(event_type="successful", occured_after=self.last_sales_check)
        if sales is False:
            return
        self.update_last_sales_check()
        for sale in sales[::-1]:
            await self.handle_new_sale(sale)
            await asyncio.sleep(2)

    # would be better to store it in the feed.db
    def update_last_sales_check(self):
        self.last_sales_check = int(datetime.datetime.now().timestamp())
        # write it in a file so we don't restart at zero when bot starts...
        with open("lastossalescheck", "w+") as f:
            f.write(str(self.last_sales_check))

    def load_last_sales_check(self):
        try:
            with open("lastossalescheck", "r") as f:
                self.last_sales_check = int(f.read())
        except FileNotFoundError:
            self.update_last_sales_check()

    async def get_events(self, event_type="", occured_after=0):
        """ 
        "   event_type can be 'created' for new auctions, 'successful' for sales, 
        "   'cancelled', 'bid_entered', 'bid_withdrawn', 'transfer', or 'approve'
        """
        s = await self.get_aiosession()
        url = self.API_URL + "/events"
        params = {
            "asset_contract_address": self.CONTRACT_ADDRESS,
            "event_type": event_type,
            "occurred_after": occured_after,
            "limit": 100,
            #"offset": 0
        }
        async with s.get(url, params=params) as r:
            if r.status != 200:
                return False
            json_resp = await r.json()
            return json_resp.get('asset_events')

    async def get_aiosession(self):
        if self.aiosession is not None:
            return self.aiosession
        self.aiosession = aiohttp.ClientSession()
        return self.aiosession

if __name__ == "__main__":
    feeder = OpenseaFeeder()
    loop = asyncio.get_event_loop()
    #loop.call_later(20, feeder.stop)
    loop.run_until_complete(feeder.run())

