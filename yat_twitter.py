import asyncio
import logging

import tweepy

import config

class TwitterBot:
    def __init__(self):
        auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
        auth.set_access_token(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_SECRET)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

    async def send_tweet(self, txt):
        #use run_in_executor to avoid blocking the rest of the code
        loop = asyncio.get_event_loop()
        try:
            status = await loop.run_in_executor(None, self.api.update_status, txt)
            logging.info("posted tweet {}".format(status.id))
        except tweepy.error.TweepError:
            logging.exception("Error while posting tweet '{}':".format(txt))

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