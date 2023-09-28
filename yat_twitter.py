import asyncio
import logging

import tweepy

import config

class TwitterBot:
    def __init__(self, access_token, access_secret):
        self.client = tweepy.Client(consumer_key=config.TWITTER_CONSUMER_KEY, consumer_secret=config.TWITTER_CONSUMER_SECRET,
            access_token=access_token, access_token_secret=access_secret)

    async def send_tweet(self, txt):
        #use run_in_executor to avoid blocking the rest of the code
        loop = asyncio.get_event_loop()
        try:
            status = await loop.run_in_executor(None, self.client.create_tweet, text=txt)
            logging.info(f"posted tweet {status.data['id']}")
        except tweepy.TweepyException:
            logging.exception(f"Error while posting tweet '{txt}':")

# Twitter only let us generate access tokens for the dev twitter account...
def user_login():
    auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
    print("Connect here:" + auth.get_authorization_url())
    verifier = input('Enter verif code:')
    auth.get_access_token(verifier)
    print("token:" + auth.access_token)
    print("secret:" + auth.access_token_secret)

if __name__ == "__main__":
    user_login()
