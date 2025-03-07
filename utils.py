import discord
import os

import nltk.sentiment
import nltk.sentiment.vader
import constants
import nltk

nltk.download("vader_lexicon", quiet=True)
sentiment_analyzer = nltk.sentiment.vader.SentimentIntensityAnalyzer()

# locate a GIF by name in the assets folder and post it given a name and the discord interaction context
async def post_gif(gif_name: str, context):
    gif_path = os.path.join("assets", f"{gif_name}.gif")
    if os.path.exists(gif_path):
        file = discord.File(gif_path)
        if isinstance(context, discord.Interaction):
            await context.response.send_message(file=file)
        elif isinstance(context, discord.Message):
            await context.channel.send(file=file)
    else:
        print(f"File {gif_path} does not exist.")
        return


# returns bool indicating if the message contains anti-lotr sentiment
async def contains_anti_lotr_sentiment(message: str):
    return (
        any(keyword in message.lower() for keyword in constants.lotr_keywords)
        and sentiment_analyzer.polarity_scores(message)["compound"] < 0
    )
