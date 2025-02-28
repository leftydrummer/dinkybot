import discord
import os


# locate a GIF by name in the assets folder and post it given a name and the discord interaction context
async def post_gif(gif_name: str, context):
    gif_path = os.path.join('assets', f"{gif_name}.gif")
    if os.path.exists(gif_path):
        file = discord.File(gif_path)
        if isinstance(context, discord.Interaction):
            await context.response.send_message(file=file)
        elif isinstance(context, discord.Message):
            await context.channel.send(file=file)
    else:
        print(f"File {gif_path} does not exist.")
        return