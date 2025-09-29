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
        await utils.post_asset_file("weird-optimized", "gif", message)

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

    await intros_channel.send(file=(await utils.get_asset_file("dy-optimized", "gif")))


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
    await utils.post_asset_file("weird-optimized", "gif", interaction)


# /dy will have dinkybot post the "dink yourself" GIF
@dinkybot.tree.command(name="dy", description="Post the DINK YOURSELF GIF")
async def dy(interaction: discord.Interaction):
    await utils.post_asset_file("dy-optimized", "gif", interaction)


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


@dinkybot.tree.command(
    name="directory",
    description="Show all public channels and threads in a tree format",
)
@discord.app_commands.describe(private="if true only you can see the response")
async def channel_map(interaction: discord.Interaction, private: bool = True):
    # Defer the interaction response since this might take a moment
    await interaction.response.defer(ephemeral=private)

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return

    # Build the channel map with a symbol key
    symbol_key = (
        "**Legend:**\n"
        "💬 Text Channel   🔊 Voice Channel   📋 Forum Channel   🎤 Stage Channel   📺 Other Channel\n"
        "🧵 Active Thread    Locked Thread\n\n"
    )
    channel_map_text = f"📋 **Directory for {guild.name}**\n" + symbol_key + "\n"

    # Get all categories and sort them
    categories = sorted([cat for cat in guild.categories], key=lambda x: x.position)

    # Get channels not in any category
    orphaned_channels = [ch for ch in guild.channels if ch.category is None and not isinstance(ch, discord.CategoryChannel)]
    orphaned_channels.sort(key=lambda x: x.position)

    # Process categories and their channels
    for category in categories:
        channel_map_text += f"📁 **{category.name}**\n"

        # Get channels in this category, sorted by position
        category_channels = sorted([ch for ch in category.channels], key=lambda x: x.position)

        for i, channel in enumerate(category_channels):
            is_last_channel = i == len(category_channels) - 1
            channel_prefix = "└── " if is_last_channel else "├── "

            # Add channel icon based on type
            if isinstance(channel, discord.TextChannel):
                channel_icon = "💬"
            elif isinstance(channel, discord.VoiceChannel):
                channel_icon = "🔊"
            elif isinstance(channel, discord.ForumChannel):
                channel_icon = "📋"
            elif isinstance(channel, discord.StageChannel):
                channel_icon = "🎤"
            else:
                channel_icon = "📺"

            channel_map_text += f"│   {channel_prefix}{channel_icon} <#{channel.id}>\n"

            # Get threads for this channel if it's a text or forum channel
            if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                try:
                    # Get active threads
                    active_threads = []
                    if hasattr(channel, 'threads'):
                        active_threads = list(channel.threads)

                    # Filter out archived threads - only show active and locked threads
                    non_archived_threads = [thread for thread in active_threads if not thread.archived]

                    if non_archived_threads:
                        non_archived_threads.sort(key=lambda x: x.name.lower())

                        for j, thread in enumerate(non_archived_threads):
                            is_last_thread = j == len(non_archived_threads) - 1
                            thread_prefix = "└── " if is_last_thread else "├── "
                            continuation = "    " if is_last_channel else "│   "

                            # Thread status indicators (only active and locked, no archived)
                            if thread.locked:
                                thread_icon = "🔒"  # Locked
                            else:
                                thread_icon = "🧵"  # Active thread

                            channel_map_text += f"│   {continuation}    {thread_prefix}{thread_icon} <#{thread.id}>\n"
                except Exception as e:
                    # If we can't access threads, just skip them
                    pass

        channel_map_text += "│\n"  # Add spacing between categories

    # Add orphaned channels (not in any category)
    if orphaned_channels:
        channel_map_text += f"📁 **No Category**\n"
        for i, channel in enumerate(orphaned_channels):
            is_last_channel = i == len(orphaned_channels) - 1
            channel_prefix = "└── " if is_last_channel else "├── "

            # Add channel icon based on type
            if isinstance(channel, discord.TextChannel):
                channel_icon = "💬"
            elif isinstance(channel, discord.VoiceChannel):
                channel_icon = "🔊"
            elif isinstance(channel, discord.ForumChannel):
                channel_icon = "📋"
            elif isinstance(channel, discord.StageChannel):
                channel_icon = "🎤"
            else:
                channel_icon = "📺"

            channel_map_text += f"    {channel_prefix}{channel_icon} <#{channel.id}>\n"

            # Get threads for this channel if it's a text or forum channel
            if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                try:
                    # Get active threads
                    active_threads = []
                    if hasattr(channel, 'threads'):
                        active_threads = list(channel.threads)

                    # Filter out archived threads - only show active and locked threads
                    non_archived_threads = [thread for thread in active_threads if not thread.archived]

                    if non_archived_threads:
                        non_archived_threads.sort(key=lambda x: x.name.lower())

                        for j, thread in enumerate(non_archived_threads):
                            is_last_thread = j == len(non_archived_threads) - 1
                            thread_prefix = "└── " if is_last_thread else "├── "
                            continuation = "    " if is_last_channel else "    "

                            # Thread status indicators (only active and locked, no archived)
                            if thread.locked:
                                thread_icon = "🔒"  # Locked
                            else:
                                thread_icon = "🧵"  # Active thread

                            channel_map_text += f"    {continuation}    {thread_prefix}{thread_icon} <#{thread.id}>\n"
                except Exception as e:
                    pass

    # Discord has a 2000 character limit for messages, so we need to split if needed
    if len(channel_map_text) <= 2000:
        await interaction.followup.send(channel_map_text, ephemeral=private)
    else:
        # Split the message into chunks
        chunks = []
        current_chunk = ""
        lines = channel_map_text.split('\n')

        for line in lines:
            if len(current_chunk + line + '\n') <= 1950:  # Leave some buffer
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + '\n'

        if current_chunk:
            chunks.append(current_chunk)

        # Send the chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                await interaction.followup.send(f"**Part {i+1}/{len(chunks)}**\n{chunk}", ephemeral=private)
            else:
                await interaction.followup.send(f"**Part {i+1}/{len(chunks)}**\n{chunk}", ephemeral=private)


# start bot event loop
token = os.getenv("BOT_TOKEN")
print(
    f"Bot token: {token}"
)  # Add this line to check if the token is being read correctly
dinkybot.run(token)
