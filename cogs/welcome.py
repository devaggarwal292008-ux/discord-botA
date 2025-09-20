import discord
from discord.ext import commands
import aiohttp
import io
import os

# Try to import Pillow safely
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

# Local asset paths (preferred)
LOCAL_BANNER = "assets/banner.png"   # Put your banner here
LOCAL_FONT = "assets/arial.ttf"      # Optional, for nicer text

# Remote fallback banner
BANNER_URL = "https://cdn.discordapp.com/attachments/1358566775708586067/1419004867766124695/IMG_20250920_141448.jpg"


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_bytes(self, url, timeout_seconds: int = 8):
        """Download bytes from a URL with timeout. Returns None on failure."""
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except Exception:
            return None
        return None

    async def generate_welcome_banner(self, member: discord.Member) -> io.BytesIO | None:
        """
        Creates a welcome banner with avatar + name + member number.
        Returns BytesIO PNG or None if failed.
        """
        if not HAVE_PIL:
            return None

        # 1. Load banner (prefer local)
        banner_bytes = None
        if os.path.exists(LOCAL_BANNER):
            try:
                with open(LOCAL_BANNER, "rb") as f:
                    banner_bytes = f.read()
            except Exception:
                banner_bytes = None
        else:
            banner_bytes = await self.fetch_bytes(BANNER_URL)

        if not banner_bytes:
            return None

        try:
            banner = Image.open(io.BytesIO(banner_bytes)).convert("RGBA")
        except Exception:
            return None

        # 2. Download avatar
        avatar_bytes = await self.fetch_bytes(str(member.display_avatar.url), timeout_seconds=6)
        if not avatar_bytes:
            return None
        try:
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        except Exception:
            return None

        # 3. Process avatar (circle crop, resize)
        avatar = ImageOps.fit(avatar, (180, 180), Image.LANCZOS)
        mask = Image.new("L", avatar.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
        avatar.putalpha(mask)

        # Paste avatar on banner (adjust position as needed)
        x = 40
        y = max(20, (banner.height // 2) - (avatar.height // 2))
        banner.paste(avatar, (x, y), avatar)

        # 4. Fonts
        try:
            if os.path.exists(LOCAL_FONT):
                font_big = ImageFont.truetype(LOCAL_FONT, 44)
                font_small = ImageFont.truetype(LOCAL_FONT, 28)
            else:
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()
        except Exception:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw = ImageDraw.Draw(banner)

        # 5. Texts
        display_name = member.display_name
        member_number = f"Member #{len(member.guild.members)}"
        welcome_text = f"Welcome, {display_name}!"

        text_x = x + avatar.width + 30
        y_top = max(20, (banner.height // 2) - 40)

        shadow_color = (0, 0, 0, 160)
        text_color = (255, 255, 255, 255)

        def draw_text_with_shadow(pos, text, font, fill=text_color):
            sx, sy = pos[0] + 2, pos[1] + 2
            draw.text((sx, sy), text, font=font, fill=shadow_color)
            draw.text(pos, text, font=font, fill=fill)

        draw_text_with_shadow((text_x, y_top), welcome_text, font_big)
        draw_text_with_shadow((text_x, y_top + 56), member_number, font_small)

        # 6. Save
        buffer = io.BytesIO()
        banner.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Find or create welcome channel
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            try:
                channel = await member.guild.create_text_channel("🚪｜welcome", overwrites=overwrites)
            except Exception:
                channel = None

        # Generate banner
        banner_file = None
        try:
            banner_bytes = await self.generate_welcome_banner(member)
            if banner_bytes:
                banner_file = discord.File(fp=banner_bytes, filename="welcome.png")
        except Exception:
            banner_file = None

        # Embed
        embed = discord.Embed(
            title="🎉 Welcome to Transcending Void!",
            description=f"Hello {member.mention}, prepare to journey into the Void!",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{len(member.guild.members)} joined!")

        # Send
        if channel:
            if banner_file:
                await channel.send(embed=embed, file=banner_file)
            else:
                await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))


