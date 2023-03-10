# data in data.json is community generated and unmoderated

from io import BytesIO
import json
import os
import textwrap

# For insurance reminder
import asyncio
import time

from itertools import cycle

import discord
from PIL import Image, ImageFont, ImageDraw, ImageSequence
from discord.ext import commands, tasks

from DiscordBotToken import BotToken

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='baidbot', intents=intents)
FoldenID = 274705127380615179
baidID = 116734104300421122  # testing purposes
MeiMeiID = 1001538703296057455
baidcologyID = 987848902315245598
baidbotdevserverID = 1072108038577725551

# cycle activity status
bot_status = cycle(
    ["with fire", "+ having fun + don't care", "with portals", "try \"hello baidbot!\"", "Half-Life 3", "Now lactose-free!", "Now with /help"])


@tasks.loop(seconds=300)
async def change_status():
    await client.change_presence(activity=discord.Game(next(bot_status)))


@client.event
async def on_ready():
    await client.tree.sync()
    await client.tree.sync(guild=discord.Object(id=baidbotdevserverID))
    print(f"Ready to use as {client.user}.")
    change_status.start()


# Ping command
@client.tree.command(name="ping", description="return bot latency")
async def ping(interaction: discord.Interaction):
    bot_latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Response time: {bot_latency}ms.")


# Favorites lookup
@client.tree.command(name="findfav", description="Finds folden's favorite everything")
async def findfav(interaction: discord.Interaction, item: str):
    data = {}
    with open("data.json", "r") as f:
        data = json.load(f)
    await interaction.response.send_message(
        f"Folden's favorite {item} is {data.get(item, 'not found. Consider using /addfav to query Foldenpaper')}.")


# Add favorites
@client.tree.command(name="addfav", description="Add a new thing to favorites list")
async def addfav(interaction: discord.Interaction, item: str):
    data = {}
    with open("data.json", "r") as fr:
        data = json.load(fr)
        fr.close()
        item = item.lower()
        # if item is not in dictionary, copy entire dictionary except the last line
        # add a comma to end of second to last line and add a new line with the added item
        # and corresponding value "None", then write it back to data.json
        if data.get(item, "failed") == "failed":
            with open("data.json", "r") as fr:
                lines = fr.readlines()[:-1]
                lines[-1] = lines[-1][:-1] + ','
                fr.close()

                item2 = None
                lines.append(f"\n  \"{item}\": \"{item2}\"\n}}")
                with open("data.json", "w") as fw:
                    fw.writelines(lines)
            await interaction.response.send_message(
                f"New thing added <@274705127380615179> Use /updatefav to add your favorite {item}!")
        else:
            await interaction.response.send_message(f"Favorite {item} already exists (**{data.get(item)}**)")


# Update favorite
@client.tree.command(name="updatefav", description="Updates favorite thing (Can only be executed by Foldenpaper)")
async def updatefav(interaction: discord.Interaction, thing: str, favorite: str):
    if (interaction.user.id == FoldenID or interaction.user.id == baidID):
        data = {}
        thing = thing.lower()
        # if favorite is NOT a URL or exception greek letter, convert to lowercase.
        if not favorite.startswith("http") and thing != "greek letter":
            favorite = favorite.lower()
        with open("data.json", "r+") as f:
            data = json.load(f)
            # Check if thing exists, if not, send fail message
            if data.get(thing, "failed") == "failed":
                await interaction.response.send_message(
                    f"Update failed! {thing} does not exist in list! Try using /addfav to create it first.")
                return
            else:
                prev_fav = data.get(thing)
                data[thing] = favorite
                f.close()
                with open("data.json", 'w') as f:
                    json.dump(data, f, indent=4)
                await interaction.response.send_message(f"Updated favorite {thing} to {favorite} from {prev_fav}")
    else:
        await interaction.response.send_message("You must be Foldenpaper to run this command!")


# Find empty favorites
@client.tree.command(name="findemptyfavs", description="Finds and lists favorites with no entry")
async def emptyfavs(interaction: discord.Interaction):
    data = {}
    emptyItems = ""
    # embed message format setup
    embed_message = discord.Embed(title="Empty Favorites", description="Foldenpaper must set these with /updatefav",
                                  color=discord.Color.orange())
    embed_message.set_author(name=f"Requested from {interaction.user.name}", icon_url=interaction.user.avatar)
    embed_message.set_thumbnail(url=interaction.guild.icon)

    with open("data.json", 'r') as f:
        data = json.load(f)
    # iterate through entire dictionary, if the favorite is listed as "None"
    # add the corresponding 'thing' to 'emptyItems' string array
    for thing, favorite in data.items():
        if favorite == "None":
            # if emptyItems is empty, dont start with a new line
            if emptyItems == "":
                emptyItems += thing
            else:
                emptyItems += ('\n' + thing)
    embed_message.add_field(name="Empty favorites for the following things:", value=emptyItems, inline=False)
    await interaction.response.send_message(embed=embed_message)


# @client.tree.command(name="listfavs", description="List available things to query")
# async def listfavs(interaction: discord.Interaction):
#    data = {}
#    favlist = ""
#    # embed message
#    embed_message = discord.Embed(title="Available things", description="All available things to use with /findfav",
#                                  color=discord.Color.orange())
#    embed_message.set_author(name=f"Requested from {interaction.user.name}", icon_url=interaction.user.avatar)
#    embed_message.set_thumbnail(url=interaction.guild.icon)
#   with open("data.json", 'r') as f:
#        data = json.load(f)
#   for thing, favorite in data.items():
#       if favlist == "":
#           favlist += thing
#       else:
#           favlist += (', ' + thing)
#   embed_message.add_field(name="Things:", value=favlist, inline=False)
#   await interaction.response.send_message(embed=embed_message)

@client.tree.command(name="meme", description="Add text to an image")
async def meme(interaction: discord.Interaction, image: discord.Attachment, toptext: str = " ",
               bottext: str = " "):
    # check if file is an image content type
    if 'image' in image.content_type:
        # defer allows discord to wait for a response longer than 3 seconds
        await interaction.response.defer()
        # download the attached image
        await image.save("tempImage.png")
        template = Image.open("tempImage.png")

        # font size scales with image width
        font_size = int(template.width / 10)
        font = ImageFont.truetype("impact.ttf", font_size)
        stroke_color = (0, 0, 0)  # black
        stroke_width = int(font_size / 10)
        text_color = (255, 255, 255)  # white
        # text margin scales with image height
        text_margin = int((template.height / 100) * 2)

        # Top Text -------------------------------------------
        # split string into multiple strings based on character length 'width'
        lines = textwrap.wrap(toptext.upper(), width=20)
        # text width and height
        tw, th = font.getsize(toptext)
        # top left text box coordinate with respect to image pixels. Top left of image is 0,0
        cx, cy = int(template.width / 2), text_margin
        # y_text offset
        y_text = (cy - th / 2)

        for line in lines:
            tw, th = font.getsize(line)
            draw = ImageDraw.Draw(template)
            draw.text((cx - tw / 2, cy), line, text_color, font=font, stroke_width=stroke_width,
                      stroke_fill=stroke_color)
            template.save("meme-generated.png")
            cy += th

        # Bottom Text -------------------------------------------
        lines = textwrap.wrap(bottext.upper(), width=20)
        tw, th = font.getsize(bottext)
        cx, cy = (template.width / 2, template.height - text_margin)
        y_text = (cy - th * len(lines))

        for line in lines:
            tw, th = font.getsize(line)
            draw = ImageDraw.Draw(template)
            draw.text((cx - tw / 2, y_text), line, text_color, font=font, stroke_width=stroke_width,
                      stroke_fill=stroke_color)
            template.save("meme-generated.png")
            y_text += th

        # Check if image is under 8Mb to be able to upload back, decrease quality of image by 5% on each pass
        if os.path.getsize(("meme-generated.png")) >= 8000000:
            img_quality = 100
            while os.path.getsize("meme-generated.jpg") >= 8000000:
                print(f"File is too large! Compressing image to {img_quality}% as JPG")
                template.save("meme-generated.jpg", "jpg", optimize=True, quality=img_quality)
                img_quality -= 5
                # if (somehow) image quality is at 0 and the file is still too large, return a message
                if img_quality == 0 and os.path.getsize("meme-generated.jpg") >= 8000000:
                    await interaction.followup.send("File is too large!")
                    return
            await interaction.followup.send(file=discord.File("meme-generated.jpg"))
            return
        await interaction.followup.send(file=discord.File("meme-generated.png"))
    else:
        await interaction.response.send_message("File must be an image!")


@client.tree.command(name="gifmeme", description="Caption a GIF")
async def memegif(interaction: discord.Interaction, gif_file: discord.Attachment, caption: str):
    if 'gif' in gif_file.content_type:
        # defer allows discord to wait for a response longer than 3 seconds
        await interaction.response.defer()

        # download the attached GIF
        await gif_file.save("input.gif")
        giftemplate = Image.open("input.gif")
        font_size = int(giftemplate.width / 10)
        font = ImageFont.truetype("Futura Condensed Extra Bold Regular.ttf", font_size)
        text_color = (0, 0, 0)  # black

        lines = textwrap.wrap(caption, width=17)
        # text width and height
        tw, th = font.getsize(caption)

        # height of white box to add at top
        padding_height = int((th * len(lines)) + th/2)
        # top left text box coordinate with respect to image pixels. Top left of image is 0,0
        cx, cy = int(giftemplate.width / 2), int((padding_height/2))
        # y_text offset
        y_text = (cy - (th/2) * len(lines))

        base_width, base_height = giftemplate.size
        new_height = base_height + padding_height

        # create empty white frame with extra height for text
        result_template = Image.new("RGBA", size=(base_width, new_height), color=(255, 255, 255))

        # draw text lines in the extra height
        for line in lines:
            tw, th = font.getsize(line)
            draw = ImageDraw.Draw(result_template)
            draw.text((cx - tw / 2, y_text), line, text_color, font=font)
            y_text += th

        # total duration of gif
        total_duration = 0
        frames = []
        for frame in ImageSequence.Iterator(giftemplate):
            # add duration of current frame to total duration
            total_duration += frame.info['duration']
            # paste each frame of gif under extra height
            temp = result_template
            temp.paste(frame, (0, padding_height))
            b = BytesIO()
            temp.save(b, format="GIF")
            temp = Image.open(b)
            frames.append(temp)
        frames[0].save('meme_out.gif', save_all=True, append_images=frames[1:], loop=giftemplate.info['loop'],
                       duration=total_duration/len(frames))
        await interaction.followup.send(file=discord.File("meme_out.gif"))
    else:
        await interaction.response.send_message("File must be a GIF!")

@client.tree.command(name="speechbubble", description="Add a speech bubble to top of an image")
async def meme(interaction: discord.Interaction, image: discord.Attachment):
    if "image" in image.content_type:
        await interaction.response.defer()
        await image.save("speechmemetemp.png")
        speech_template = Image.open("speechmemetemp.png")
        speech_bubble = Image.open("SBOverlay.png")
        speech_bubble = speech_bubble.resize((speech_template.width, int(speech_template.height/3)))
        # Check if original image has transparency, use alpha_composite() if so
        if speech_template.mode != "RBGA":
            speech_template.paste(speech_bubble, (0, 0), speech_bubble)
        else:
            speech_template.alpha_composite(speech_bubble, (0, 0))
        speech_template.save("SBresult.png")

        # Check if image is under 8Mb to be able to upload back, decrease quality of image by 5% on each pass
        if os.path.getsize(("SBresult.png")) >= 8000000:
            img_quality = 100
            while os.path.getsize("SBresult.jpg") >= 8000000:
                print(f"File is too large! Compressing image to {img_quality}% as JPG")
                speech_template.save("SBresult.jpg", "jpg", optimize=True, quality=img_quality)
                img_quality -= 5
                # if (somehow) image quality is at 0 and the file is still too large, return a message
                if img_quality == 0 and os.path.getsize("SBresult.jpg") >= 8000000:
                    await interaction.followup.send("File is too large!")
                    return
            await interaction.followup.send(file=discord.File("SBresult.jpg"))
            return
        await interaction.followup.send(file=discord.File("SBresult.png"))
    else:
        await interaction.response.send_message("File must be an image!")

@client.tree.command(name="insurance", description="Remind yourself to collect Tarkov insurance tomorrow")
async def insuranceremind(interaction: discord.Interaction):
    one_day = 86400
    one_hour = 3600
    epoch_time = int(time.time())
    await interaction.response.send_message(f"I will remind you at <t:{epoch_time + one_day + (one_hour*5)}:t> tomorrow to collect your insurance", ephemeral=True)
    await asyncio.sleep(one_day + (one_hour * 5))
    await interaction.user.send(f"Collect your Tarkov insurance from yesterday's session at <t:{epoch_time}:t>!")

@client.tree.command(name="help", description="How to use commands")
async def help(interaction: discord.Interaction):
    # embed message
    embed_message = discord.Embed(title="Command Help", color=discord.Color.orange())
    embed_message.set_author(name=f"Requested from {interaction.user.name}", icon_url=interaction.user.avatar)
    embed_message.set_thumbnail(url=client.user.avatar)
    embed_message.add_field(name="**Folden favorites:---------------------------**",
                            value="**/findfav** - Find folden's favorite everything"
                            "\n**/addfav** - Add a new category to favorites (Folden will need to use /updatefav)"
                            "\n**/updatefav** - Update a category's favorite item (Can only be executed by Foldenpaper)"
                            "\n**/findemptyfavs** - List all favorites categories which are empty (Folden will need to update with /updatefav"
                            , inline=False)
    embed_message.add_field(name="**Meme:---------------------------**",
                            value="**/meme** - Add top text and/or bottom text to an image in the classic style"
                            "\n**/gifmeme** - Add text above a gif in a margin in the classic meme gif style"
                            "\n**/speechbubble** - Add a speech bubble to the top of your image for meme responses"
                            , inline=False)
    embed_message.add_field(name="**Misc:---------------------------**",
                            value="**/insurance** - Used for Tarkov players to get notified when their insurance is ready to claim (from Prapor)"
                            "\n**/ping** - Returns bot latency"
                            "\n**/help** - List command help"
                            , inline=False)
    await interaction.response.send_message(embed=embed_message, ephemeral=True)


# On message...
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    message.content = message.content.lower()
    if message.content.startswith('hello baidbot') or message.content.startswith('hi baidbot'):
        await message.channel.send(f"Hi <@{message.author.id}>! :heart:")

    if message.content.lower() == "who asked" or message.content.lower() == "didnt ask" or message.content.lower() == "didn't ask":
        await message.channel.send(
            "https://tenor.com/view/i-asked-halo-halo-infinite-master-chief-chimp-zone-gif-24941497")



client.run(BotToken)
