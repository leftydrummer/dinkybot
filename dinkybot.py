"""
Made with ❤️ by Neill for the Dinky Podcast community
"""

import utils
import constants
import discord
import nltk
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
nltk.download("vader_lexicon")


intents = discord.Intents.default()
intents.message_content = True
dinkybot = commands.Bot(command_prefix="!", intents=intents)


"""
EVENT HANDLERS @
"""


# Runs after the bot is authenticated and synced with Discord
# For all guilds, find the general channel and post the 'ready' message
@dinkybot.event
async def on_ready():
    # Sync the application commands defined here
    try:
        synced = await dinkybot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

    for guild in dinkybot.guilds:
        print(guild.id)
        print(
            f"{dinkybot.user} is connected to the following guild: {guild.name} (id: {guild.id})"
        )
        for channel in guild.text_channels:
            print(f"Found text channel: {channel.name} (id: {channel.id})")


@dinkybot.event
async def on_message(message):

    # If a message in the server contains the string "this is really weird" or "this is weird", post the 'weird' GIF and reply to the user
    if "this is really weird" in str.lower(
        message.content
    ) or "this is weird" in str.lower(message.content):
        await message.channel.send(f"It sure is, {message.author.mention}")
        await utils.post_gif("weird-optimized", message)

    # Post joke reply if messsage contains negative sentiment and LOTR keywords
    if await utils.contains_anti_lotr_sentiment(message.content):
        await message.reply(constants.LOTR_WARNING, mention_author=True)

    # make sure any commands in the message are processed
    await dinkybot.process_commands(message)


"""
SLASH COMMANDS
"""


# /weird will have dinkybot post the "this is really weird" GIF
@dinkybot.tree.command(name="weird", description="Posts the 'this is weird' GIF")
async def weird(interaction: discord.Interaction):
    await utils.post_gif("weird-optimized", interaction)


# /dy will have dinkybot post the "dink yourself" GIF
@dinkybot.tree.command(name="dy", description="Post the DINK YOURSELF GIF")
async def dy(interaction: discord.Interaction):
    await utils.post_gif("dy-optimized", interaction)


# /hello will say hello to the user ephemerally
@dinkybot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello, {interaction.user.mention}! You mentioned me", ephemeral=True
    )


dinkybot.run(os.getenv("BOT_TOKEN"))
