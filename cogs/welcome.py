import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import os

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # If you saved the banner in your bot folder
        self.banner_path = "banner_background.png"

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            channel = await member.guild.create_text_channel("🚪｜welcome", overwrites=overwrites)

        # Load background banner
        if os.path.exists(self.banner_path):
            base = Image.open(self.banner_path).convert("RGBA")
        else:
            base = Image.new("RGBA", (900, 250), (30, 30, 30, 255))

        draw = ImageDraw.Draw(base)

        # Fonts
        font_big = ImageFont.truetype("arial.ttf", 40)  # update path/font if needed
        font_small = ImageFont.truetype("arial.ttf", 25)

        # Avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(str(member.display_avatar.url)) as resp:
                avatar_bytes = await resp.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((180, 180))

        # Make avatar circle mask
        mask = Image.new("L", avatar.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

        base.paste(avatar, (20, 35), mask)

        # Add text onto banner
        draw.text((230, 80), f"Welcome {member.name}!", font=font_big, fill=(255,255,255))
        draw.text((230, 150), f"You are member #{len(member.guild.members)}", font=font_small, fill=(200,200,200))

        buffer = io.BytesIO()
        base.save(buffer, "PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="welcome_card.png")

        await channel.send(
            content=f"🎉 Welcome to **{member.guild.name}**, {member.mention}!",
            file=file
        )

async def setup(bot):
    await bot.add_cog(Welcome(bot))

