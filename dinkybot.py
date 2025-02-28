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
@dinkybot.event
async def on_ready():
    channel_id = 1334231390711185580
    channel = dinkybot.get_channel(channel_id)
    await channel.send("Hello World! I'm online now.")

    # Sync the application commands defined here
    try:
        synced = await dinkybot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# If a message in the server contains the string "this is really weird" or "this is weird", post the Jillie GIF
@dinkybot.event
async def on_message(message):
    if "this is really weird" in message.content or "this is weird" in message.content:
        await utils.post_gif("weird", message)
    await dinkybot.process_commands(message)

"""
SLASH COMMANDS
"""

# /ping will have dinkybot respond with its network latency in ms
@dinkybot.tree.command(name="ping", description="Responds with the bot's latency.")
async def ping(interaction: discord.Interaction):
    """Responds with the bot's latency."""
    await interaction.response.send_message(f"Pong! Latency: {round(dinkybot.latency * 1000)}ms")


# /hello will have dinkybot respond with hello, mentioning the user
@dinkybot.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")


# /weird will have dinkybot post the "this is really weird" GIF
@dinkybot.tree.command(name="weird", description="Posts the Jillie GIF")
async def weird(interaction: discord.Interaction):
    await utils.post_gif("weird", interaction)


# /dy will have dinkybot post the "dink yourself" GIF
@dinkybot.tree.command(name="dy", description="Post the DINK YOURSELF GIF")
async def dy(interaction: discord.Interaction):
    await utils.post_gif("dy", interaction)


dinkybot.run(os.getenv("DISCORD_TOKEN"))
