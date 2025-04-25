"""
Made with ❤️ by Neill for the Dinky Podcast community
"""

import utils
import constants
import discord
import os
import feedparser
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

import platform
import psutil

load_dotenv()

# Create a bot instance with needed intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
dinkybot = commands.Bot(command_prefix="!", intents=intents)

# Initialize global variables
bot_guild = None
podcast_alerts_channel = None
intros_channel = None
general_channel = None
podcast_feed = None
stored_latest_rss_entry = None
bot_start_time = datetime.now(timezone.utc)


### EVENT HANDLERS ###


# Runs after the bot is authenticated and synced with Discord
@dinkybot.event
async def on_ready():

    global bot_guild
    global podcast_alerts_channel
    global podcast_feed
    global intros_channel
    global general_channel

    # Get the guild and dedicated channel objects
    bot_guild = dinkybot.guilds[0]
    podcast_alerts_channel = await utils.get_channel_by_name(
        bot_guild, constants.PODCAST_NOTIFICATION_CHANNEL_NAME
    )
    intros_channel = await utils.get_channel_by_name(
        bot_guild, constants.INTROS_CHANNEL_NAME
    )
    general_channel = await utils.get_channel_by_name(
        bot_guild, constants.GENERAL_PURPOSE_CHANNEL_NAME
    )

    # Parse the podcast RSS feed
    podcast_feed = feedparser.parse(os.getenv("PODCAST_RSS_URL"))

    # Sync the application commands to Discord
    try:
        synced = await dinkybot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

    # Start tasks
    rss_checker.start()

    # For debugging purposes, print out the guilds and channels the bot is connected to
    for guild in dinkybot.guilds:
        print(
            f"{dinkybot.user} is connected to the following guild: {guild.name} (id: {guild.id})"
        )
        for channel in guild.text_channels:
            print(f"Found text channel: {channel.name} (id: {channel.id})")

    # Send a message to the general channel to indicate the bot is ready
    if constants.SHOW_READY_MSG:
        await general_channel.send(constants.BOT_READY_MSG)


# Runs when a message is posted to any channel the bot has access to
# Recieves a message object as an argument
@dinkybot.event
async def on_message(message):

    # Ignore messages sent by the bot itself
    if message.author == dinkybot.user:
        return

    # If a message in the server contains the string "this is really weird" or "this is weird", post the 'weird' GIF and reply to the user
    if "this is really weird" in str.lower(
        message.content
    ) or "this is weird" in str.lower(message.content):
        await message.channel.send(f"It sure is, {message.author.mention}")
        await utils.post_gif("weird-optimized", message)

    # Need to improve sentiment analysis before re-enabling

    # # Post joke reply if messsage contains negative sentiment and LOTR keywords
    # if await utils.contains_anti_lotr_sentiment(message.content):
    #     await message.reply(constants.LOTR_WARNING, mention_author=True)

    # make sure any commands in the message are processed
    await dinkybot.process_commands(message)


# Runs when a new member joins the server
@dinkybot.event
async def on_member_join(member):
    print(f"{member} has joined the server!")
    global intros_channel
    await intros_channel.send(
        f"Welcome to the server, {member.mention}! We welcome you. Type `/help` to learn more about me. DINK YOURSELF!"
    )

    await intros_channel.send(file=(await utils.get_gif_file("dy-optimized")))


### TASKS ###


# Check the podcast RSS feed every 10 minutes
# If there is a new entry, send an embed to the podcast-chatter channel
@tasks.loop(minutes=10)
async def rss_checker():
    global stored_latest_rss_entry
    global podcast_alerts_channel
    global podcast_feed

    # Parse the podcast RSS feed
    podcast_feed = feedparser.parse(os.getenv("PODCAST_RSS_URL"))

    # Check the parsed feed for any entries
    if podcast_feed.entries:

        # Get the latest entry from the feed
        fetched_latest_rss_entry = podcast_feed.entries[0]
        podcast_embed = await utils.rss_entry_embed(fetched_latest_rss_entry)

        # If there is no stored latest entry, store the fetched latest entry
        if not stored_latest_rss_entry:
            stored_latest_rss_entry = fetched_latest_rss_entry
        else:
            # If the stored latest entry's guid is different from the fetched latest entry's guid, update the stored latest entry and send an alert
            if stored_latest_rss_entry.get("guid") != fetched_latest_rss_entry.get(
                "guid"
            ):
                stored_latest_rss_entry = fetched_latest_rss_entry
                if podcast_alerts_channel:
                    await utils.post_new_episode_alert(
                        podcast_alerts_channel, podcast_embed
                    )
    return


### SLASH COMMANDS ###


# /weird will have dinkybot post the "this is really weird" GIF
@dinkybot.tree.command(name="weird", description="Posts the 'this is weird' GIF")
async def weird(interaction: discord.Interaction):
    await utils.post_asset_file("weird-optimized", interaction)


# /dy will have dinkybot post the "dink yourself" GIF
@dinkybot.tree.command(name="dy", description="Post the DINK YOURSELF GIF")
async def dy(interaction: discord.Interaction):
    await utils.post_gif("dy-optimized", interaction)


# /gf will have dinkybot post the "get fucked" PNG
@dinkybot.tree.command(name="gf", description="Post the GET FUCKED image")
async def gf(interaction: discord.Interaction):
    await utils.post_asset_file("gf-optimized", "png", interaction)


# /latest-episode will give the user the podcast embed for the latest episode ephemerally
@dinkybot.tree.command(
    name="latest-episode",
    description="Get the latest podcast episode",
)
@discord.app_commands.describe(private="if true only you can see the response")
async def latest_episode(interaction: discord.Interaction, private: bool = True):
    global stored_latest_rss_entry

    if stored_latest_rss_entry:
        podcast_embed = await utils.rss_entry_embed(stored_latest_rss_entry)
        await interaction.response.send_message(embed=podcast_embed, ephemeral=private)
    else:
        await interaction.response.send_message(
            "No podcast episodes found.", ephemeral=private
        )


# /search-episodes will allow the user to search the catalog by title
@dinkybot.tree.command(
    name="search-episodes",
    description="Search the podcast catalog by title",
)
@discord.app_commands.describe(
    query="The search query for the episode title",
    private="if true only you can see the response",
)
async def search_episodes(
    interaction: discord.Interaction, query: str, private: bool = True
):
    global podcast_feed

    # Defer the interaction response
    await interaction.response.defer(ephemeral=private)

    # Parse the podcast RSS feed
    podcast_feed = feedparser.parse(os.getenv("PODCAST_RSS_URL"))

    # Search for episodes that match the query
    closest_match_entry = await utils.podcast_search(
        entries=podcast_feed.entries, search_term=query
    )

    if closest_match_entry:
        podcast_embed = await utils.rss_entry_embed(closest_match_entry)
        await interaction.followup.send(embed=podcast_embed, ephemeral=private)
    else:
        await interaction.followup.send(
            "No matching podcast episodes found.", ephemeral=private
        )


# /help will show the user bot help info
@dinkybot.tree.command(
    name="help",
    description="Show bot help info",
)
@discord.app_commands.describe(private="if true only you can see the response")
async def help(interaction: discord.Interaction, private: bool = True):
    # Load bothelp.md file
    with open("bothelp.md", "r") as f:
        help_text = f.read()

    # Split the help text into chunks of 2000 characters or less
    chunks = [help_text[i : i + 2000] for i in range(0, len(help_text), 2000)]

    # Send the first chunk as an initial response
    await interaction.response.send_message(chunks[0], ephemeral=private)

    # Send the remaining chunks as follow-up messages
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=private)

    return


@dinkybot.tree.command(
    name="video-link",
    description="Post a video link with a nice inline embed",
)
async def video_link(interaction: discord.Interaction):
    await interaction.response.send_modal(utils.VideoLinkModal())


@dinkybot.tree.command(
    name="debug-info",
    description="Get debug/environment info about the bot",
)
async def debug_info(interaction: discord.Interaction):
    # Calculate uptime using timezone-aware datetime
    now = datetime.now(timezone.utc)
    uptime = now - bot_start_time
    uptime_str = str(uptime).split(".")[0]  # Remove microseconds

    # Gather system info
    python_version = platform.python_version()
    dpy_version = discord.__version__
    os_info = f"{platform.system()} {platform.release()}"
    cpu = platform.processor() or "Unknown"
    ram = psutil.virtual_memory().total // (1024**2)  # in MB
    current_time = now.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    hostname = platform.node()

    # Create embed with timezone-aware timestamp
    embed = discord.Embed(
        title="🛠️ DinkyBot Debug Info", color=discord.Color.blue(), timestamp=now
    )
    embed.add_field(name="Bot Name", value=interaction.client.user.name, inline=True)
    embed.add_field(name="Bot ID", value=interaction.client.user.id, inline=True)
    embed.add_field(name="Uptime (UTC)", value=uptime_str, inline=True)
    embed.add_field(
        name="Guilds", value=str(len(interaction.client.guilds)), inline=True
    )
    embed.add_field(name="Python", value=python_version, inline=True)
    embed.add_field(name="discord.py", value=dpy_version, inline=True)
    embed.add_field(name="OS", value=os_info, inline=True)
    embed.add_field(name="CPU", value=cpu, inline=True)
    embed.add_field(name="RAM", value=f"{ram} MB", inline=True)
    embed.add_field(name="Local Time", value=current_time, inline=True)
    embed.add_field(name="Hostname", value=hostname, inline=True)
    embed.set_footer(text="UTC Timestamp")

    await interaction.response.send_message(embed=embed, ephemeral=True)
    return


# start bot event loop
token = os.getenv("BOT_TOKEN")
print(
    f"Bot token: {token}"
)  # Add this line to check if the token is being read correctly
dinkybot.run(token)
