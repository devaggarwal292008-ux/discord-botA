import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import os
import traceback

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _measure_text(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
        """Safe text size measurement (works across Pillow versions)."""
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except Exception:
            try:
                return draw.textsize(text, font=font)
            except Exception:
                try:
                    return font.getsize(text)
                except Exception:
                    return (len(text) * 12, 30)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            channel = member.guild.system_channel

        try:
            # Banner path (place banner.jpeg in repo root)
            banner_path = os.path.join(os.path.dirname(__file__), "..", "banner.jpeg")
            if not os.path.exists(banner_path):
                if channel:
                    await channel.send(f"🎉 Welcome to **{member.guild.name}** {member.mention}!")
                return

            background = Image.open(banner_path).convert("RGBA")
            W, H = background.size

            # Avatar
            avatar_asset = member.display_avatar.replace(size=256)
            avatar_bytes = await avatar_asset.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            avatar = avatar.resize((220, 220))  # slightly bigger

            mask = Image.new("L", avatar.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

            # Avatar position (higher, centered)
            avatar_x = (W - avatar.size[0]) // 2
            avatar_y = H // 4 - avatar.size[1] // 2
            background.paste(avatar, (avatar_x, avatar_y), mask)

            # Fonts
            font_path = os.path.join(os.path.dirname(__file__), "..", "Poppins-Bold.ttf")
            try:
                font_big = ImageFont.truetype(font_path, 70)
                font_small = ImageFont.truetype(font_path, 45)
            except Exception:
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw = ImageDraw.Draw(background)

            text = f"Welcome {member.name}!"
            subtext = f"You are member #{len(member.guild.members)}"

            w1, h1 = self._measure_text(draw, text, font_big)
            w2, h2 = self._measure_text(draw, subtext, font_small)

            text_x = (W - w1) // 2
            subtext_x = (W - w2) // 2

            text_y = avatar_y + avatar.size[1] + 30
            subtext_y = text_y + h1 + 15

            # Draw with shadow
            shadow = 3
            draw.text((text_x + shadow, text_y + shadow), text, font=font_big, fill="black")
            draw.text((text_x, text_y), text, font=font_big, fill="white")

            draw.text((subtext_x + shadow, subtext_y + shadow), subtext, font=font_small, fill="black")
            draw.text((subtext_x, subtext_y), subtext, font=font_small, fill="white")

            # Save + send
            buffer = io.BytesIO()
            background.save(buffer, "PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="welcome.png")
            if channel:
                await channel.send(content=f"🎉 Welcome to **{member.guild.name}** {member.mention}!", file=file)

        except Exception as exc:
            traceback.print_exc()
            if channel:
                await channel.send(f"🎉 Welcome to **{member.guild.name}** {member.mention}!\n⚠️ (welcome image failed: {exc})")

async def setup(bot):
    await bot.add_cog(Welcome(bot))









