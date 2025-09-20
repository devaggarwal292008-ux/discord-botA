import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import os

BANNER_URL = "https://cdn.discordapp.com/attachments/1358566775708586067/1419004867766124695/IMG_20250920_141448.jpg"
FONT_PATH = "arial.ttf"

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_font(self):
        """Download arial.ttf if not already present"""
        if not os.path.exists(FONT_PATH):
            async with aiohttp.ClientSession() as session:
                url = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/arial.ttf"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(FONT_PATH, "wb") as f:
                            f.write(await resp.read())

    async def generate_welcome_banner(self, member):
        # Ensure font is available
        await self.ensure_font()

        # Download banner
        async with aiohttp.ClientSession() as session:
            async with session.get(BANNER_URL) as resp:
                banner_bytes = await resp.read()
        banner = Image.open(io.BytesIO(banner_bytes)).convert("RGBA")

        # Download avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(str(member.display_avatar.url)) as resp:
                avatar_bytes = await resp.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((180, 180))

        # Make avatar circular
        mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
        avatar.putalpha(mask)

        # Paste avatar onto banner
        banner.paste(avatar, (50, 100), avatar)

        # Draw text
        draw = ImageDraw.Draw(banner)
        font = ImageFont.truetype(FONT_PATH, 40)

        username = str(member.name)
        member_number = f"Member #{len(member.guild.members)}"

        draw.text((260, 120), f"Welcome, {username}!", font=font, fill="white")
        draw.text((260, 180), member_number, font=font, fill="white")

        # Save to BytesIO
        buffer = io.BytesIO()
        banner.save(buffer, "PNG")
        buffer.seek(0)
        return buffer

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(send_messages=True, view_channel=True)
            }
            channel = await member.guild.create_text_channel("🚪｜welcome", overwrites=overwrites)

        banner_file = await self.generate_welcome_banner(member)

        embed = discord.Embed(
            title="🎉 Welcome to Transcending Void!",
            description=f"Hello {member.mention}, prepare to journey into the Void. "
                        "Join our tournaments and enjoy your stay!",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{len(member.guild.members)} joined!")

        await channel.send(embed=embed, file=discord.File(banner_file, "welcome.png"))

async def setup(bot):
    await bot.add_cog(Welcome(bot))

