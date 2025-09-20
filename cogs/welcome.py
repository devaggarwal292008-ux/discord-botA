import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io

BANNER_URL = "https://cdn.discordapp.com/attachments/1358566775708586067/1419004867766124695/IMG_20250920_141448.jpg?ex=68d02ec4&is=68cedd44&hm=dd0e724ff1154099a5a7691fd682dde3be005242c37f76737812f25e9c3b27e6"

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(send_messages=True, view_channel=True)
            }
            channel = await member.guild.create_text_channel("🚪｜welcome", overwrites=overwrites)

        # Fetch banner
        async with aiohttp.ClientSession() as session:
            async with session.get(BANNER_URL) as resp:
                banner_bytes = await resp.read()
        banner = Image.open(io.BytesIO(banner_bytes)).convert("RGBA")

        # Fetch member avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(str(member.display_avatar.url)) as resp:
                avatar_bytes = await resp.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((200, 200))

        # Make circular avatar
        mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
        avatar.putalpha(mask)

        # Paste avatar on banner
        banner.paste(avatar, (50, 50), avatar)

        # Draw text
        draw = ImageDraw.Draw(banner)
        try:
            font = ImageFont.truetype("arial.ttf", 50)
        except:
            font = ImageFont.load_default()

        username = f"Welcome {member.name}!"
        member_count = f"You are our {len(member.guild.members)}th member 🎉"
        draw.text((300, 80), username, font=font, fill="white")
        draw.text((300, 150), member_count, font=font, fill="white")

        # Save to BytesIO
        with io.BytesIO() as image_binary:
            banner.save(image_binary, "PNG")
            image_binary.seek(0)
            await channel.send(file=discord.File(fp=image_binary, filename="welcome.png"))

async def setup(bot):
    await bot.add_cog(Welcome(bot))



