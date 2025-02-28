""" 
Made with ❤️ by Neill for the Dinky Podcast community 

https://dinkypod.com

DINK YOURSELF! 

"""

import utils
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

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
        for channel in guild.channels:
            if channel.name == "general" and isinstance(channel, discord.TextChannel):
                await channel.send("Hello World! I'm awake!")
                break


# If a message in the server contains the string "this is really weird" or "this is weird", post the Jillie GIF
@dinkybot.event
async def on_message(message):
    if "this is really weird" in str.lower(message.content) or "this is weird" in str.lower(message.content):
        await utils.post_gif("weird", message)
    await dinkybot.process_commands(message)


"""
SLASH COMMANDS
"""


# /weird will have dinkybot post the "this is really weird" GIF
@dinkybot.tree.command(name="weird", description="Posts the 'this is weird' GIF")
async def weird(interaction: discord.Interaction):
    await utils.post_gif("weird", interaction)


# /dy will have dinkybot post the "dink yourself" GIF
@dinkybot.tree.command(name="dy", description="Post the DINK YOURSELF GIF")
async def dy(interaction: discord.Interaction):
    await utils.post_gif("dy", interaction)


dinkybot.run(os.getenv("DISCORD_TOKEN"))
