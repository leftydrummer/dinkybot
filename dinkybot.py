""" 
Made with ❤️ by Neill for the Dinky Podcast community 
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
        print(
            f"{dinkybot.user} is connected to the following guild: {guild.name} (id: {guild.id})"
        )
        for channel in guild.text_channels:
            print(f"Found text channel: {channel.name} (id: {channel.id})")


# If a message in the server contains the string "this is really weird" or "this is weird", post the 'weird' GIF and reply to the user
@dinkybot.event
async def on_message(message):

    if "this is really weird" in str.lower(
        message.content
    ) or "this is weird" in str.lower(message.content):
        await message.channel.send(f"It sure is, {message.author.mention}")
        await utils.post_gif("weird-optimized", message)
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


dinkybot.run(os.getenv("BOT_TOKEN"))
