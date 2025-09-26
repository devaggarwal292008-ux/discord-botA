import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import traceback

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _measure_text(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
        """Safe text size measurement across Pillow versions."""
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

    async def _get_welcome_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Find or create the 🚪｜welcome channel."""
        target_name = "🚪｜welcome"
        ch = discord.utils.get(guild.text_channels, name=target_name)
        if ch:
            return ch

        for c in guild.text_channels:
            if "welcome" in c.name.lower():
                return c

        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            return await guild.create_text_channel(target_name, overwrites=overwrites)
        except Exception:
            return guild.system_channel

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = await self._get_welcome_channel(guild)
        if not channel:
            return

        try:
            # Use BANNER2.jpeg
            banner_path = os.path.join(os.path.dirname(__file__), "..", "BANNER2.jpeg")
            if not os.path.exists(banner_path):
                await channel.send(f"🎉 Welcome to **{guild.name}** {member.mention}!")
                return

            background = Image.open(banner_path).convert("RGBA")
            W, H = background.size

            # Avatar
            avatar_asset = member.display_avatar.replace(size=256)
            avatar_bytes = await avatar_asset.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

            avatar_size = int(H * 0.5)
            avatar = ImageOps.fit(avatar, (avatar_size, avatar_size), Image.LANCZOS)

            # Circle mask
            mask = Image.new("L", avatar.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

            # Border
            border = 8
            bordered = Image.new("RGBA", (avatar_size + 2*border, avatar_size + 2*border), (255, 255, 255, 0))
            ring = ImageDraw.Draw(bordered)
            ring.ellipse((0, 0, bordered.size[0]-1, bordered.size[1]-1), fill=(255, 255, 255, 255))
            bordered.paste(avatar, (border, border), mask)

            avatar_x = int(W * 0.08)
            avatar_y = int((H - bordered.size[1]) // 2)
            background.paste(bordered, (avatar_x, avatar_y), bordered)

            # Fonts
            font_path = os.path.join(os.path.dirname(__file__), "..", "Poppins-Bold.ttf")
            try:
                font_big = ImageFont.truetype(font_path, int(H * 0.12))
                font_small = ImageFont.truetype(font_path, int(H * 0.07))
            except Exception:
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw = ImageDraw.Draw(background)
            text = f"Welcome {member.display_name}!"
            subtext = f"You are member #{len(guild.members)}"

            w1, h1 = self._measure_text(draw, text, font_big)
            w2, h2 = self._measure_text(draw, subtext, font_small)

            text_x = avatar_x + bordered.size[0] + int(W * 0.05)
            block_h = h1 + h2 + int(h1 * 0.3)
            text_y = (H - block_h) // 2

            # Shadow + text
            shadow = 3
            draw.text((text_x + shadow, text_y + shadow), text, font=font_big, fill="black")
            draw.text((text_x, text_y), text, font=font_big, fill="white")

            draw.text((text_x + shadow, text_y + h1 + 15 + shadow), subtext, font=font_small, fill="black")
            draw.text((text_x, text_y + h1 + 15), subtext, font=font_small, fill="white")

            # Save and send
            buffer = io.BytesIO()
            background.save(buffer, "PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="welcome.png")
            await channel.send(content=f"🎉 Welcome to **{guild.name}**, {member.mention}!", file=file)

        except Exception as exc:
            traceback.print_exc()
            await channel.send(f"🎉 Welcome to **{guild.name}** {member.mention}!\n⚠️ (banner failed: {exc})")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
