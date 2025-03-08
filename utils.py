import discord
import os
import nltk.sentiment
import nltk.sentiment.vader
import constants
import nltk
import feedparser
from markdownify import markdownify as md
import random

# download the vader lexicon for sentiment analysis
nltk.download("vader_lexicon", quiet=True)
sentiment_analyzer = nltk.sentiment.vader.SentimentIntensityAnalyzer()


# locate a GIF by name in the assets folder and post it given a name and the discord Interaction context
async def post_gif(gif_name: str, context):
    try:
        file = get_gif_file(gif_name)
        if isinstance(context, discord.Interaction):
            await context.response.send_message(file=file)
        elif isinstance(context, discord.Message):
            await context.channel.send(file=file)
    except FileNotFoundError as e:
        print(e)
        return


async def get_gif_file(gif_name: str) -> discord.File:
    gif_path = os.path.join("assets", f"{gif_name}.gif")
    if os.path.exists(gif_path):
        return discord.File(gif_path)
    else:
        raise FileNotFoundError(f"File {gif_path} does not exist.")


# returns bool indicating if the message contains anti-lotr sentiment
async def contains_anti_lotr_sentiment(message: str):
    return (
        any(keyword in message.lower() for keyword in constants.LOTR_KEYWORDS)
        and sentiment_analyzer.polarity_scores(message)["compound"] < 0
    )


# generate an embed for a podcast given a title, description, url, and image url
async def generate_podcast_embed(
    title: str, description: str, url: str, image_url: str
):
    embed = discord.Embed(
        title=title, url=url, description=md(description), color=discord.Color.pink()
    )
    embed.set_image(url=image_url)
    return embed


# get link embed by passing in Feedparser entry
async def rss_entry_embed(entry: feedparser.FeedParserDict):
    return await generate_podcast_embed(
        title=entry.get("title"),
        description=entry.get("summary"),
        url=entry.get("link"),
        image_url=entry.get("image", {}).get("href"),
    )


# get channel object by name given a guild object and a channel name
async def get_channel_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.text_channels, name=name)


# given a channel object, post the new episode alert and the embed to that channel
async def post_new_episode_alert(channel: discord.TextChannel, embed: discord.Embed):
    await channel.send(constants.NEW_PODCAST_ALERT)
    await channel.send(embed=embed)


# search for a podcast in the feed by title
async def podcast_search(entries: list[feedparser.FeedParserDict], search_term: str):

    best_match = None

    title_contains_search_term_list = [
        entry for entry in entries if search_term.lower() in entry.get("title").lower()
    ]

    if title_contains_search_term_list:
        # set best match to a random entry that contains the search term
        best_match = random.choice(title_contains_search_term_list)

    return best_match


# get user object by name given a guild object and a user name
async def get_user_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.members, name=name)
