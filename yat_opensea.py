import asyncio
import logging
import aiohttp
import datetime

from yat_twitter import TwitterBot
from yat_api import YatAPI
from yat_utils import get_yat_from_url, split_yat, twitter_sanitize
import config

class OpenseaFeeder:
    REFRESH_INTERVAL = 200
    API_URL = "https://api.opensea.io/api/v1"
    CONTRACT_ADDRESS = "0x7d256d82b32d8003d1ca1a1526ed211e6e0da9e2"
    TWITTER_TEMPLATE = {
        "txt": "\"{yatname}\" was just bought for {tokenprice} {tokensymbol} (${usdprice})!\n\n{infos}\n\n#yat #nft #opensea\n{oslink}",
        # url length = 23, len('"" was just bought for 0.0000000000000000000 AAAAAA ($999999)!\n\n#yat #nft #opensea\n') = 83
        # max infos length ~ 40
        "noname_length": 83 + 23 + 40,
        "max_length": 240
    }
    DISCORD_TEMPLATE = {
        "txt": "{emoji_id} was just bought for {tokenprice} {tokensymbol} (${usdprice}) on OpenSea!",
        # discord links are not shortened (i don't think someone will (or even can) put a 1900char name but we never know)
        "noname_length": 75,
        "max_length": 2000
    }

    def __init__(self, discord=None):
        self.task = None
        self.aiosession = None

        # remember start time so we can filter out the yats bought before that we haven't stored
        self.startup_time = int(datetime.datetime.now().timestamp())
        self.seen_sale_ids = set()

        self.yat_api = YatAPI()
        self.twitter = TwitterBot(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_SECRET)
        self.twipeater = TwitterBot(config.TWIPEATER_ACCESS_TOKEN, config.TWIPEATER_ACCESS_SECRET)
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
                await self.yat_api.close()
                self.task = None
                logging.info("Stopped OpenseaFeeder task")
                break
            except Exception as e:
                logging.exception("Error during OpenseaFeeder operation:")
                await asyncio.sleep(5)

    def fill_template(self, template, s, m=None, i=None, emoji_id="?"):
        token_price=int(s['total_price']) / (10 ** s['payment_token']['decimals'])
        if m:
            traits = {t['trait_type']: t['value'] for t in m.get('attributes', [])}
        else:
            traits = {}
        if i:
            rs = "\n💯 RS {}".format(i['rhythm_score']) if i.get('rhythm_score') else ""
        else:
            rs = "\n💯 RS {}".format(traits['Rhythm Score']) if traits.get('Rhythm Score') else ""

        gen = "📅 {}".format(traits['Generation']) if traits.get('Generation') else ""
        origin = "\n🐣 Origin: {}".format(traits.get('Origin').replace('_', ' ').title()) if traits.get('Origin') else ""
        shape = "\n✨ Shape: {}".format(traits.get('Shape')) if traits.get('Shape') else ""
        infos = "{gen}{rs}{origin}{shape}".format(rs=rs, gen=gen, origin=origin, shape=shape)

        # todo: maybe add filtering to avoid mentions/url/hashtag injections
        name = s['asset']['name']
        if name is None:
            name = emoji_id
        name = twitter_sanitize(name)
        if template['noname_length'] + len(name) > template['max_length']:
            name = name[:20] + " ... " + name[-20:]
        return template['txt'].format(
            oslink=s['asset']['permalink'],
            yatlink=s['asset']['external_link'],
            imglink=s['asset']['image_original_url'],
            vidlink=s['asset']['animation_original_url'],
            yatname=name,
            emoji_id=emoji_id,
            tokenprice=token_price,
            tokensymbol=s['payment_token']['symbol'],
            usdprice=round(token_price*float(s['payment_token']['usd_price'])),
            infos=infos
        )

    async def handle_new_sale(self, s):
        token_id = s['asset']['token_id']
        if token_id in config.TOKEN_BLACKLIST:
            logging.info("Skipping sale of blacklisted token {}".format(token_id))
            return
        # we need to fetch both metadata and infos to get exact RS and origin :/
        metadata = await self.yat_api.get_metadata(token_id)
        if metadata:
            yat_url = metadata.get('external_link')
        else:
            yat_url = s['asset'].get('external_link')
        emoji_id = get_yat_from_url(yat_url)
        infos = await self.yat_api.get_infos(emoji_id)
        token_price=int(s['total_price']) / (10 ** s['payment_token']['decimals'])
        usd_price = round(token_price*float(s['payment_token']['usd_price']))

        if self.twitter is not None and usd_price >= config.TWITTER_MIN_USD_SALE_PRICE:
            # not really async yet but should be at some point (depends on tweepy)
            twitter_txt = self.fill_template(self.TWITTER_TEMPLATE, s, metadata, infos, emoji_id)
            await self.twitter.send_tweet(twitter_txt)

        if self.twipeater is not None and len(set(split_yat(emoji_id))) == 1:
            # this is a repeater
            twipeater_txt = self.fill_template(self.TWITTER_TEMPLATE, s, metadata, infos, emoji_id)
            await self.twipeater.send_tweet(twipeater_txt)

        if self.discord is not None:
            discord_txt = self.fill_template(self.DISCORD_TEMPLATE, s, metadata, infos, emoji_id)
            await self.discord.feeder.send(discord_txt, feed_type=1)

    async def check_new_sales(self):
        sales = await self.get_events(event_type="successful", occured_after=self.startup_time)
        if sales is False:
            return
        # reverse order and filter out the sales we've already seen
        sales = [sale for sale in sales[::-1] if sale['id'] not in self.seen_sale_ids]
        for sale in sales:
            self.seen_sale_ids.add(sale['id'])
            await self.handle_new_sale(sale)
            await asyncio.sleep(2)

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
            "limit": 25,
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

