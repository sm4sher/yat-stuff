from discord.ext.commands import Bot, guild_only
from discord.ext.commands.errors import MissingRequiredArgument, BadArgument, CommandError, MissingPermissions, CommandNotFound
from discord import File, Game, TextChannel, Member, Intents
from datetime import datetime

from yat_image import parse_string, check_seq, make_img
from yat_pattern import get_yats_from_pattern, scan
from yat_api import paste
from yat_scanner import YatScanner
from yat_feeder import YatFeeder

import config
import logging
import typing

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s: %(message)s", filename="yat_bot.log", level=logging.INFO)

class CommandException(Exception):
    pass

class YatBot(Bot):
    feed_started = False
    async def on_ready(self):
        activity = Game("{}view".format(config.PREFIX), start=datetime.now())
        await self.change_presence(activity=activity)

        if config.START_SCANNER:
            self.scanner = YatScanner(self)
            self.scanner.start()
        if not self.feed_started:
            self.feeder = YatFeeder(self)
            self.feeder.start()
            self.feed_started = True
        logging.info('bot is ready')

    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            await ctx.reply('Unknown command "{}". Type {} to see a list of commands'.format(
                config.PREFIX+ctx.invoked_with, config.PREFIX+'help'))

bot = YatBot(command_prefix=config.PREFIX)

@bot.command()
async def invite(ctx):
    await ctx.reply("Invite me on your server by clicking this link: {}".format(
        config.INVITE_URL))
    

@bot.command()
async def view(ctx, *, arg):
    """ +yatview [your yat] """
    logging.info('view cmd in {} by {} with arg: {}'.format(ctx.guild if ctx.guild else 'DM', ctx.author, arg))
    arg = arg.replace(' ', '')
    emo_seq = parse_string(arg)
    res, msg = check_seq(emo_seq)
    if not res:
        await ctx.reply("{} {}".format(ctx.author.mention, msg))
        return
    try:
        img = make_img(emo_seq)
    except:
        logging.exception("Error while creating yat image")
        await ctx.reply("Sorry there was an error...")
        return
    await ctx.reply(file=File(img, filename="beautifulyat.png"))

@view.error
async def view_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        await ctx.reply("You didn't provide a Yat to display")
    else:
        logging.exception("Error while creating yat image", error)
        await ctx.reply("Sorry there was an error....")

@bot.command()
async def pattern(ctx, *, pattern):
    """ +yatpattern [pattern] - Check availability of Yats matching pattern """
    logging.info('pattern cmd in {} by {}'.format(ctx.guild if ctx.guild else 'DM', ctx.author))
    if ctx.author.id not in config.PATTERN_COMMAND_AUTHORIZED:
        await ctx.reply("Sorry you don't have the permission to use this command. Send a DM to sm4sher#0967 if you're interested!")
        return
    try:
        yats = get_yats_from_pattern(pattern)
        if len(yats) > 20:
            await ctx.reply("Checking {} Yats, this can take some time!".format(len(yats)))
        res = await bot.loop.run_in_executor(None, scan, yats)
    except:
        logging.exception("Error while performing pattern search")
        await ctx.reply("{} sorry there was an error...")
        return
    if len(res) > 1000:
        link = paste(res)
        msg = "Your pattern search is done! Results were too long for discord, you can view them here {}".format(link)
    else:
        msg = res
    await ctx.reply(msg)

@pattern.error
async def pattern_error(ctx, error):
    logging.warning('Error in pattern command:' + str(error))
    if isinstance(error, MissingRequiredArgument):
        await ctx.reply("You didn't provide a pattern to search")
    else:
        await ctx.reply("Sorry there was an error....")

@bot.command(hidden=True)
async def scanstatus(ctx):
    if bot.scanner.is_running():
        msg = "Scanner is curently running.\nLast scan: {}\n"
    else:
        msg = "Scanner isn't curently running.\nLast scan: {}\n"
    msg += "Coming soon emojis: {}\n".format(', '.join(bot.scanner.COMING_SOON))
    if ctx.author.id in config.NEW_EMOJI_NOTIF:
        msg += "You are subscribed to the notifications."
    else:
        msg += "You aren't subscribed to the notifications. Send a DM to sm4sher#0967 if you're interested!"
    await ctx.reply(msg.format('{}s ago'.format((datetime.now()-bot.scanner.last_scan).seconds) if bot.scanner.last_scan else 'never'))

@bot.command()
async def feed(ctx, count: typing.Optional[int]=10):
    """ Print the 10 most recent Yat purchases """
    logging.info('feed cmd in {} by {}'.format(ctx.guild if ctx.guild else 'DM', ctx.author))
    recent = bot.feeder.get_recent_yats(limit=min(count, 100))
    if not recent:
        await ctx.reply('Sorry there was an error, try again later')
        return
    recent.reverse()
    out = 'Recently purchased Yats:\n'
    out += '\n'.join(["{} (RS{})".format(y.get('emoji_id'), y.get('rhythm_score')) for y in recent]) 
    out += "\nUse '{}livefeed on/off channel' to set up live updates".format(config.PREFIX)
    await ctx.reply(out)

@bot.command()
@guild_only()
async def livefeed(ctx, switch: bool, channel: TextChannel):
    """ Set up a livefeed of Yats purchases in the channel of your choice """
    logging.info('livefeed cmd in {} by {}'.format(ctx.guild if ctx.guild else 'DM', ctx.author))
    if not ctx.author.permissions_in(channel).manage_channels:
        raise MissingPermissions("You must have the Manage Channels discord permission to set up a live feed")

    if switch:
        bot.feeder.register_chan(channel, ctx.author)
        await ctx.reply("The Yat livefeed has been enabled successfuly")
    else:
        res, msg = bot.feeder.unregister_chan(channel)
        if res:
            await ctx.reply("The Yat livefeed has been disabled successfuly")
        else:
            await ctx.reply(msg)

@livefeed.error
async def livefeed_error(ctx, error):
    if isinstance(error, CommandError):
        await ctx.reply(str(error))
    else:
        logging.exception('Error in livefeed command', error)
        await ctx.reply("Sorry there was an error setting up the live feed...")



if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)
