import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import os

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Find or create welcome channel
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(send_messages=True, view_channel=True)
            }
            channel = await member.guild.create_text_channel("🚪｜welcome", overwrites=overwrites)

        # Load the banner you uploaded
        banner_path = "1000383155.jpg"
        if not os.path.exists(banner_path):
            await channel.send("⚠️ Banner image not found! Please upload `1000383155.jpg` in the bot folder.")
            return

        background = Image.open(banner_path).convert("RGBA")

        # Get member avatar
        avatar_asset = member.display_avatar.replace(size=128)
        avatar_bytes = await avatar_asset.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((150, 150))

        # Circle mask for avatar
        mask = Image.new("L", avatar.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
        background.paste(avatar, (50, 100), mask)

        # Text drawing
        draw = ImageDraw.Draw(background)
        try:
            font_big = ImageFont.truetype("arial.ttf", 60)  # Uses Arial if present
            font_small = ImageFont.truetype("arial.ttf", 40)
        except:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()

        text = f"Welcome {member.name}!"
        subtext = f"You are member #{len(member.guild.members)}"

        draw.text((250, 120), text, font=font_big, fill="white")
        draw.text((250, 200), subtext, font=font_small, fill="white")

        # Save image to buffer
        buffer = io.BytesIO()
        background.save(buffer, "PNG")
        buffer.seek(0)

        # Send banner
        file = discord.File(fp=buffer, filename="welcome.png")
        await channel.send(content=f"🎉 Welcome to **{member.guild.name}** {member.mention}!", file=file)

async def setup(bot):
    await bot.add_cog(Welcome(bot))




