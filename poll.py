"""
MIT License

Copyright (c) 2018 Breee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord
from discord.ext import commands
import logging
import threading
import time

bot = commands.Bot(description="Raid Leader, a Bot for Pokemon Go raid organization.",
                   command_prefix=("!raid-", "!r-"))

config_file = open('config.conf')
log_file = 'pollbot.log'
token = ""
playing = ""

for line in config_file:
    if line.startswith("token="):
        token = line[line.find("=") + 1:].rstrip("\n")
    if line.startswith("playing="):
        playing = line[line.find("=") + 1:].rstrip("\n")

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Timeout that specifies when messages in SAVED_MESSAGES are removed.
TIMEOUT = 60 * 60 * 10

# Timestep in which the bot will update messages.
MSG_UPDATE_INTERVAL = 100

# Dictionary that maps the numblock emojis to a number.
EMOJI_TO_NUMBER = {
    "\U00000031\U000020E3": 0,
    "\U00000032\U000020E3": 1,
    "\U00000033\U000020E3": 2,
    "\U00000034\U000020E3": 3,
    "\U00000035\U000020E3": 4,
    "\U00000036\U000020E3": 5,
    "\U00000037\U000020E3": 6,
    "\U00000038\U000020E3": 7,
    "\U00000039\U000020E3": 8,
    "\U0001F51F": 9
}

# Reverse of EMOJI_TO_NUMBER
NUMBER_TO_EMOJI = {
    0: "\U00000031\U000020E3",
    1: "\U00000032\U000020E3",
    2: "\U00000033\U000020E3",
    3: "\U00000034\U000020E3",
    4: "\U00000035\U000020E3",
    5: "\U00000036\U000020E3",
    6: "\U00000037\U000020E3",
    7: "\U00000038\U000020E3",
    8: "\U00000039\U000020E3",
    9: "\U0001F51F",
}

# Dictionary that maps the people emojis to a number.
# The emojis in this dict are used in the raid-poll to express the amount of extra people someone
#  brings to a raid.
PEOPLE_EMOJI_TO_NUMBER = {
    "\U0001F57A": 1,
    "\U0001F46D": 2,
    "\U0001F46A": 3,
    "\U0001F468\U0000200D\U0001F469\U0000200D\U0001F467\U0000200D\U0001F466": 4
}

SAVED_MESSAGES = []
POLL_ID_COUNTER = 0


def update_msgs():
    for message in SAVED_MESSAGES:
        if time.time() - message[2] > TIMEOUT:
            SAVED_MESSAGES.remove(message)
    threading.Timer(MSG_UPDATE_INTERVAL, update_msgs).start()


async def edit_msg(message, embed):
    await bot.edit_message(message, message.content, embed=embed)


@bot.event
async def on_ready():
    logging.info("Logged in as " + bot.user.name + " " + bot.user.id)
    print("Bot has logged in.")
    print("discord.py version " + discord.__version__)
    update_msgs()
    await bot.change_presence(game=discord.Game(name=playing))


@bot.command()
async def ping():
    await bot.say("I'm awake!")


@bot.command(pass_context=True)
async def poll(ctx, poll_title, *, timepoints_string=""):
    global POLL_ID_COUNTER
    POLL_ID_COUNTER += 1
    message = ctx.message
    title = poll_title
    timepoints_list = timepoints_string.split(" ")
    if not timepoints_string:
        # ERROR 1
        await bot.say('ERROR 1:\n'
                      'No vote options provided.\n'
                      '\n'
                      'Command used by %s:\n'
                      '%s \n'
                      '\n'
                      'Usage:\n !raid-poll "<poll title>" <option_1> ... <option_10>\n'
                      '\n'
                      'Example:\n !raid-poll "Kyogre Jump & twist" 19:00 19:15 19:30 19:40' % (
                          ctx.message.author.mention, ctx.message.content))
        return
    if len(timepoints_list) > len(EMOJI_TO_NUMBER):
        # ERROR 2
        await bot.say('ERROR 2:\n'
                      'The maximum number of vote options is 10.\n'
                      '\n'
                      'Command used by %s:\n'
                      '%s \n'
                      '\n'
                      'Usage:\n !raid-poll "<poll title>" <option_1> ... <option_10>\n'
                      '\n'
                      'Example:\n !raid-poll "Kyogre Jump & twist" 19:00 19:15 19:30 19:40' % (
                          ctx.message.author.mention, ctx.message.content))
        return

    embed, emoji_to_embed_field = create_raid_embed(title=title, timepoints=timepoints_list)
    message = await bot.send_message(message.channel,
                                     content="Created poll #%s." % POLL_ID_COUNTER,
                                     embed=embed)
    msg_summary = [message, [], time.time(), None, embed, emoji_to_embed_field]
    SAVED_MESSAGES.append(msg_summary)

    sorted_emoji = [(k, EMOJI_TO_NUMBER[k]) for k in
                    sorted(EMOJI_TO_NUMBER, key=EMOJI_TO_NUMBER.get)]

    for emoji, n in sorted_emoji:
        if n <= len(timepoints_list) - 1:
            await bot.add_reaction(message, emoji)
    sorted_people_emoji = [(k, PEOPLE_EMOJI_TO_NUMBER[k]) for k in
                           sorted(PEOPLE_EMOJI_TO_NUMBER, key=PEOPLE_EMOJI_TO_NUMBER.get)]
    for emoji, n in sorted_people_emoji:
        await bot.add_reaction(message, emoji)


def create_raid_embed(title, timepoints, description=""):
    emoji_to_field = dict()
    embed = discord.Embed(title=title, colour=discord.Colour(0x700000), description=description)
    for i in range(len(timepoints)):
        emoji = NUMBER_TO_EMOJI[i]
        timepoint = timepoints[i]
        fieldname = "%s %s" % (emoji, timepoint)
        embed.add_field(name=fieldname, value="-", inline=False)
        emoji_to_field[emoji] = fieldname

    return embed, emoji_to_field


def update_embed(embed, emoji_to_fields, reactions):
    """
    Function which will take the current embed of a raid-poll and return an updated embed.
    :param embed: embed created by the function create_raid_embed.
    :param emoji_to_fields: a dictionary which maps reaction emojis to the fields of an embed.
    :param reactions: a list of tuples of the form [(reaction_0, user_0),...,(reaction_n, user_n)]
    :return:
    """
    new_embed = discord.Embed(title=embed.title, colour=discord.Colour(0x700000),
                              description=embed.description)
    # list of users which reacted to a certain field in the embed
    reaction_to_user = {}
    # list of users which come not alone
    people_to_user = {}
    # for each reaction, user tuple in reactions, we fill the dictionaries reaction_to_user, people
    # _to_user.
    for reaction, user in reactions:
        # add a user to reaction_to_user if he reacted with an emoji that equals an emoji mapped
        # to a field in the embed
        if reaction.emoji in emoji_to_fields.keys():
            reaction_to_user.setdefault(emoji_to_fields[reaction.emoji], []).append(user.name)
            if user.name not in people_to_user.keys():
                # by default every user comes alone. i.e. counts as one person.
                people_to_user[user.name] = 1
        # add a user to people_to_user, if he reacted with an emoji that equals an emoji of the
        # PEOPLE_EMOJI_TO_NUMBER dict.
        if reaction.emoji in PEOPLE_EMOJI_TO_NUMBER.keys():
            if user.name in people_to_user:
                people_to_user[user.name] += PEOPLE_EMOJI_TO_NUMBER[reaction.emoji]
            else:
                people_to_user[user.name] = 1 + PEOPLE_EMOJI_TO_NUMBER[reaction.emoji]

    for field in embed.fields:
        if field.name in reaction_to_user.keys():
            total = 0
            people = ""
            for i, user in enumerate(reaction_to_user[field.name]):
                people += user + " [%d] " % people_to_user[user]
                if i < len(reaction_to_user[field.name]) - 1:
                    people += ", "
                total += people_to_user[user]
            new_embed.add_field(name=field.name + " [%d]" % total, value=people, inline=False)
        else:
            new_embed.add_field(name=field.name, value="-", inline=False)
    return new_embed


@bot.event
async def on_message_delete(message):
    for msg in SAVED_MESSAGES:
        if msg[0].content == message.content:
            logger.info("Deleted message %s" % msg[0])
            await bot.delete_message(msg[3])
            SAVED_MESSAGES.remove(msg)


@bot.event
async def on_reaction_add(reaction, user):
    if user != bot.user:
        if reaction.emoji in EMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER:
            for message in SAVED_MESSAGES:
                if reaction.message.content == message[0].content:
                    message[1].append((reaction, user))
                    embed = update_embed(message[4], message[5], message[1])
                    if message[1] is not None:
                        await edit_msg(reaction.message, embed)


@bot.event
async def on_reaction_remove(reaction, user):
    if user != bot.user:
        if reaction.emoji in EMOJI_TO_NUMBER or reaction.emoji in PEOPLE_EMOJI_TO_NUMBER:
            for message in SAVED_MESSAGES:
                if reaction.message.content == message[0].content:
                    message[1].remove((reaction, user))
                    embed = update_embed(message[4], message[5], message[1])
                    if message[1] is not None:
                        await edit_msg(reaction.message, embed)


bot.run(token)
