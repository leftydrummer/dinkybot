import discord
import os
import constants
import feedparser
from markdownify import markdownify as md
import random
import yt_dlp
import uuid
import shutil
from pathlib import Path
from ffmpeg4discord.twopass import TwoPass
import aiohttp
import asyncio
import subprocess

# # download the vader lexicon for sentiment analysis
# nltk.download("vader_lexicon", quiet=True)
# sentiment_analyzer = nltk.sentiment.vader.SentimentIntensityAnalyzer()


# locate an asset by name and extentsion in the assets folder and post it 
async def post_asset_file(asset_file_name: str, file_ext: str, context):
    try:
        file = await get_asset_file(asset_file_name, file_ext)
        if isinstance(context, discord.Interaction):
            await context.response.send_message(file=file)
        elif isinstance(context, discord.Message):
            await context.channel.send(file=file)
    except FileNotFoundError as e:
        print(e)
        return


async def get_asset_file(file_name: str, file_extension: str) -> discord.File:
    file_path = os.path.join("assets", f"{file_name}.{file_extension}")
    if os.path.exists(file_path):
        return discord.File(file_path)
    else:
        raise FileNotFoundError(f"Asset file {file_name}.{file_extension} not found.")


# returns bool indicating if the message contains anti-lotr sentiment
# async def contains_anti_lotr_sentiment(message: str):
#     return (
#         any(keyword in message.lower() for keyword in constants.LOTR_KEYWORDS)
#         and sentiment_analyzer.polarity_scores(message)["compound"] < -0.6
#     )


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
    for channel in guild.channels:
        if name.lower() in channel.name.lower():
            return channel
    return None


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


# Generate a random 6-digit positive number
def generate_random_number():
    return random.randint(100000, 999999)


# download video with yt-dlp, save to temp folder
# returns the file downloaded file path
async def download_video(url: str):
    file_id = str(uuid.uuid4())[:8]  # Generate a random 8-character ID
    file_name = f"dinkybot_extract_{file_id}.mp4"
    
    def _download_sync():
        ydl_opts = {
            "format": "best",
            "outtmpl": os.path.join("temp", file_name),
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return os.path.join("temp", file_name)
    
    # Run yt-dlp download in thread pool to avoid blocking
    return await asyncio.to_thread(_download_sync)


# compress video file to meet Discord's file size limits
async def compress_video_for_discord(input_file_path: str, target_mb: int = 10) -> tuple[str, float]:
    """
    Compress a video file to meet Discord's file size limits.
    Returns tuple of (output_filename, final_size_mb)
    """
    input_path = Path(input_file_path)
    output_path = input_path.parent / f"compressed_{input_path.name}"
    
    def _compress_sync():
        try:
            # Get file size in MB for logging
            file_size_mb = input_path.stat().st_size / (1024 * 1024)
            print(f"[COMPRESSION] Starting compression of {file_size_mb:.1f}MB file to {target_mb}MB target")
            print(f"[COMPRESSION] Input: {input_path}")
            print(f"[COMPRESSION] Output: {output_path}")
            
            # Use TwoPass for compression - pass Path object for filename
            twopass = TwoPass(
                filename=input_path,  # Pass Path object, not string
                target_filesize=target_mb,
                output=str(output_path),   # Keep output as string
                codec="libx264",
                verbose=True,
            )
            
            print(f"[COMPRESSION] TwoPass object created successfully")
            final_size = twopass.run()
            print(f"[COMPRESSION] TwoPass completed successfully, final size: {final_size}MB")
            
            return str(output_path), final_size
                
        except Exception as e:
            print(f"[COMPRESSION ERROR] TwoPass compression failed: {e}")
            print(f"[COMPRESSION ERROR] Error type: {type(e)}")
            raise Exception(f"Video compression failed: {e}")
    
    # Run compression in thread pool to avoid blocking
    return await asyncio.to_thread(_compress_sync)


# given a url, get the yt-dlp extract_info for the video
async def get_video_info(url: str):
    def _get_info_sync():
        ydl_opts = {
            "format": "best",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info
    
    # Run yt-dlp in thread pool to avoid blocking
    return await asyncio.to_thread(_get_info_sync)


# leverage get_video_info to return a boolean indicating if the video is supported for download by yt-dlp
async def is_video_supported(url: str) -> bool:
    try:
        info = await get_video_info(url)
        return True
    except yt_dlp.utils.DownloadError:
        return False
    except yt_dlp.utils.ExtractorError:
        return False
    except Exception as e:
        print(f"Error checking video support: {e}")
        return False


# Define a modal for collecting the video URL
class VideoLinkModal(discord.ui.Modal, title="Post a Video Link"):
    url = discord.ui.TextInput(
        label="Video URL",
        placeholder="Enter the URL of the video",
        required=True,
    )

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        # Defer the interaction response
        await interaction.response.defer()

        video_is_supported = await is_video_supported(self.url.value)

        # Check if the URL is valid
        if not video_is_supported:
            # If the URL is not valid, send an error message
            await interaction.followup.send(
                "I wasn't able to use this link. Sorry! 😭.",
                ephemeral=True,
            )
            return

        try:
            await interaction.followup.send(f"Getting video data...", ephemeral=True)

            video_metadata = await get_video_info(self.url.value)

            await interaction.followup.send(
                f"Video source is {video_metadata['extractor_key']}, extraction is supported",
                ephemeral=True,
            )

            await interaction.followup.send(
                f"Processing video...This might take a while", ephemeral=True
            )
            downloaded_file = await download_video(self.url.value)
        except Exception as e:
            # Log the full error to console
            print(f"[VIDEO ERROR] Video processing failed: {e}")
            print(f"[VIDEO ERROR] Error type: {type(e)}")
            print(f"[VIDEO ERROR] URL: {self.url.value}")
            
            # Alert the user about the problem
            await interaction.followup.send(
                f"An error occurred while processing the video: {str(e)}",
                ephemeral=True,
            )
            return

        # Create an embed for the video link
        embed = discord.Embed(
            title=f"{video_metadata["extractor_key"]} - {video_metadata["title"]}",
            url=self.url.value,
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Enjoy your video!")

        # Try to post the video file and embed
        try:
            await interaction.followup.send(
                content=f"Hey I grabbed that video for you {interaction.user.mention}! 🧙‍♂️🪄",
                file=discord.File(downloaded_file),
                embed=embed,
                ephemeral=False,
            )
        except discord.HTTPException as e:
            # Check if it's a 413 "Request Entity Too Large" error
            if e.status == 413:
                await interaction.followup.send(
                    f"Video file is too large for Discord. Attempting to compress...",
                    ephemeral=True,
                )
                
                try:
                    # Compress the video to 10MB
                    compressed_file, final_size = await compress_video_for_discord(downloaded_file, target_mb=10)
                    
                    await interaction.followup.send(
                        f"Video compressed to {final_size:.1f}MB. Uploading compressed version...",
                        ephemeral=True,
                    )
                    
                    # Try uploading the compressed version
                    await interaction.followup.send(
                        content=f"Hey I grabbed that video for you {interaction.user.mention}! 🧙‍♂️🪄 (Compressed to fit Discord limits)",
                        file=discord.File(compressed_file),
                        embed=embed,
                        ephemeral=False,
                    )
                    
                    # Clean up the compressed file
                    os.remove(compressed_file)
                    
                except Exception as compress_error:
                    await interaction.followup.send(
                        f"Failed to compress video: {str(compress_error)}. The video may be too long or complex to compress to Discord's limits.",
                        ephemeral=True,
                    )
            else:
                # Re-raise other HTTP exceptions
                raise e

        # Clear all files from temp folder after sending the video
        shutil.rmtree("temp")
        os.makedirs("temp", exist_ok=True)
