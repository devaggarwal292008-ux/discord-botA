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
        """
        Robust text measurement:
        - try draw.textbbox (newer Pillow)
        - fall back to draw.textsize
        - fall back to font.getsize
        - final fallback: estimate
        """
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
                    # very rough fallback
                    return (max(100, len(text) * 10), 24)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Find or create welcome channel
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(send_messages=True, view_channel=True)
            }
            try:
                channel = await member.guild.create_text_channel("🚪｜welcome", overwrites=overwrites)
            except Exception:
                # If creation fails, try to use system channel or bail gracefully
                channel = member.guild.system_channel

        try:
            # --- Load banner (fallback to plain embed if not found) ---
            banner_path = os.path.join(os.path.dirname(__file__), "..", "banner.jpeg")
            if not os.path.exists(banner_path):
                # fallback: always send a simple message so channel receives something
                if channel:
                    await channel.send(f"🎉 Welcome to **{member.guild.name}** {member.mention}!")
                return

            background = Image.open(banner_path).convert("RGBA")
            W, H = background.size

            # --- Get avatar ---
            avatar_asset = member.display_avatar.replace(size=256)
            avatar_bytes = await avatar_asset.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            avatar = avatar.resize((200, 200))

            # Circle mask
            mask = Image.new("L", avatar.size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

            # Center avatar near top
            avatar_x = (W - avatar.size[0]) // 2
            avatar_y = 60
            background.paste(avatar, (avatar_x, avatar_y), mask)

            # --- Draw text ---
            draw = ImageDraw.Draw(background)

            font_path = os.path.join(os.path.dirname(__file__), "..", "Poppins-Bold.ttf")
            try:
                font_big = ImageFont.truetype(font_path, 70)
                font_small = ImageFont.truetype(font_path, 45)
            except Exception:
                # fallback to default font if custom not available
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            text = f"Welcome {member.name}!"
            subtext = f"You are member #{len(member.guild.members)}"

            # measure text sizes robustly
            w1, h1 = self._measure_text(draw, text, font_big)
            w2, h2 = self._measure_text(draw, subtext, font_small)

            text_x = (W - w1) // 2
            subtext_x = (W - w2) // 2
            text_y = avatar_y + avatar.size[1] + 40
            subtext_y = text_y + h1 + 20

            # Draw shadow + text for readability
            shadow = 3
            draw.text((text_x + shadow, text_y + shadow), text, font=font_big, fill="black")
            draw.text((text_x, text_y), text, font=font_big, fill="white")

            draw.text((subtext_x + shadow, subtext_y + shadow), subtext, font=font_small, fill="black")
            draw.text((subtext_x, subtext_y), subtext, font=font_small, fill="white")

            # --- Save & send ---
            buffer = io.BytesIO()
            background.save(buffer, "PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="welcome.png")
            if channel:
                await channel.send(content=f"🎉 Welcome to **{member.guild.name}** {member.mention}!", file=file)
        except Exception as exc:
            # log to console for debugging and still send fallback message
            print("Error in welcome cog:", file=__import__("sys").stderr)
            traceback.print_exc()
            if channel:
                try:
                    await channel.send(f"🎉 Welcome to **{member.guild.name}** {member.mention}!\n⚠️ (welcome image failed: {exc})")
                except Exception:
                    # last-resort: try system channel or do nothing
                    pass

async def setup(bot):
    await bot.add_cog(Welcome(bot))








