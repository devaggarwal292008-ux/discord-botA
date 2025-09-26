import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import traceback

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_welcome_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Find 🚪｜welcome channel or fallback."""
        ch = discord.utils.get(guild.text_channels, name="🚪｜welcome")
        if ch:
            return ch
        for c in guild.text_channels:
            if "welcome" in c.name.lower():
                return c
        return guild.system_channel

    def _fit_text(self, draw: ImageDraw.ImageDraw, text: str, max_width: int, font_path: str, base_size: int) -> ImageFont.ImageFont:
        """Shrink font size until text fits max_width."""
        font_size = base_size
        while font_size > 10:
            font = ImageFont.truetype(font_path, font_size)
            w, _ = draw.textsize(text, font=font)
            if w <= max_width:
                return font
            font_size -= 2
        return ImageFont.truetype(font_path, 10)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = await self._get_welcome_channel(guild)
        if not channel:
            return

        try:
            # Banner background
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

            avatar_size = int(H * 0.8)  # occupy 80% of banner height
            avatar = ImageOps.fit(avatar, (avatar_size, avatar_size), Image.LANCZOS)

            # Circle mask + border
            mask = Image.new("L", avatar.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)

            border = 8
            bordered = Image.new("RGBA", (avatar_size + 2*border, avatar_size + 2*border), (0, 0, 0, 0))
            ring = ImageDraw.Draw(bordered)
            ring.ellipse((0, 0, bordered.size[0]-1, bordered.size[1]-1), fill=(255, 255, 255, 255))
            bordered.paste(avatar, (border, border), mask)

            # Place avatar
            avatar_x = int(W * 0.05)
            avatar_y = (H - bordered.size[1]) // 2
            background.paste(bordered, (avatar_x, avatar_y), bordered)

            # Fonts
            font_path = os.path.join(os.path.dirname(__file__), "..", "Poppins-Bold.ttf")
            draw = ImageDraw.Draw(background)

            # Text
            text = f"HEY @{member.display_name.upper()} WELCOME TO {guild.name.upper()}"
            subtext = f"YOU ARE OUR {len(guild.members)}TH MEMBER!"

            text_x = avatar_x + bordered.size[0] + int(W * 0.05)
            max_width = W - text_x - int(W * 0.05)

            # Auto-fit fonts
            font_big = self._fit_text(draw, text, max_width, font_path, int(H * 0.22))
            font_small = self._fit_text(draw, subtext, max_width, font_path, int(H * 0.13))

            # Positions
            text_y = avatar_y + int(H * 0.15)
            subtext_y = text_y + font_big.size + int(H * 0.05)

            # Draw with shadow
            shadow = 3
            draw.text((text_x+shadow, text_y+shadow), text, font=font_big, fill="black")
            draw.text((text_x, text_y), text, font=font_big, fill="white")

            draw.text((text_x+shadow, subtext_y+shadow), subtext, font=font_small, fill="black")
            draw.text((text_x, subtext_y), subtext, font=font_small, fill="white")

            # Save to buffer
            buffer = io.BytesIO()
            background.save(buffer, "PNG")
            buffer.seek(0)

            # Send
            file = discord.File(fp=buffer, filename="welcome.png")
            await channel.send(content=f"👋 Welcome {member.mention}!", file=file)

        except Exception as exc:
            traceback.print_exc()
            await channel.send(f"👋 Welcome to **{guild.name}** {member.mention}!\n⚠️ (banner failed: {exc})")

async def setup(bot):
    await bot.add_cog(Welcome(bot))

