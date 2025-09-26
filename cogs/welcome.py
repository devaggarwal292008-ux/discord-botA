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
        """Find welcome channel by exact name or fallback to first match."""
        ch = discord.utils.get(guild.text_channels, name="🚪｜welcome")
        if ch:
            return ch
        for c in guild.text_channels:
            if "welcome" in c.name.lower():
                return c
        return guild.system_channel

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = await self._get_welcome_channel(guild)
        if not channel:
            print(f"[WELCOME] ⚠️ No welcome channel found in {guild.name}")
            return

        try:
            # Paths
            base_dir = os.path.dirname(os.path.dirname(__file__))
            banner_path = os.path.join(base_dir, "BANNER2.jpg")
            font_path = os.path.join(base_dir, "Asgrike.otf")  # 🔥 Load Asgrike.otf

            if not os.path.exists(banner_path):
                print(f"[WELCOME] ❌ Banner not found at {banner_path}")
                await channel.send(f"👋 Welcome {member.mention}! (Banner missing)")
                return

            background = Image.open(banner_path).convert("RGBA")
            W, H = background.size
            print(f"[WELCOME] ✅ Loaded banner ({W}x{H})")

            # Avatar
            avatar_asset = member.display_avatar.replace(size=256)
            avatar_bytes = await avatar_asset.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

            avatar_size = int(H * 0.6)  # 60% of banner height
            avatar = ImageOps.fit(avatar, (avatar_size, avatar_size), Image.LANCZOS)

            mask = Image.new("L", avatar.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)

            # White border
            border = 6
            bordered = Image.new("RGBA", (avatar_size + 2*border, avatar_size + 2*border), (0, 0, 0, 0))
            ring = ImageDraw.Draw(bordered)
            ring.ellipse((0, 0, bordered.size[0]-1, bordered.size[1]-1), fill=(255, 255, 255, 255))
            bordered.paste(avatar, (border, border), mask)

            avatar_x = int(W * 0.04)
            avatar_y = (H - bordered.size[1]) // 2
            background.paste(bordered, (avatar_x, avatar_y), bordered)

            # Fonts
            try:
                font_big = ImageFont.truetype(font_path, int(H * 0.15))   # 15% height
                font_small = ImageFont.truetype(font_path, int(H * 0.08)) # 8% height
                print("[WELCOME] ✅ Loaded custom font: Asgrike.otf")
            except Exception as e:
                print(f"[WELCOME] ❌ Font error: {e} (falling back)")
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw = ImageDraw.Draw(background)

            text = f"HEY @{member.display_name.upper()} WELCOME TO {guild.name.upper()}"
            subtext = f"YOU ARE OUR {len(guild.members)}TH MEMBER!"

            # Text positions
            text_x = avatar_x + bordered.size[0] + int(W * 0.05)
            text_y = avatar_y + int(H * 0.2)
            subtext_y = text_y + font_big.size + int(H * 0.05)

            # Shadowed text
            shadow = 2
            draw.text((text_x+shadow, text_y+shadow), text, font=font_big, fill="black")
            draw.text((text_x, text_y), text, font=font_big, fill="white")

            draw.text((text_x+shadow, subtext_y+shadow), subtext, font=font_small, fill="black")
            draw.text((text_x, subtext_y), subtext, font=font_small, fill="white")

            # Save + send
            buffer = io.BytesIO()
            background.save(buffer, "PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="welcome.png")
            await channel.send(content=f"🎉 Welcome to **{guild.name}** {member.mention}!", file=file)

            print(f"[WELCOME] ✅ Sent banner for {member.display_name} in {guild.name}")

        except Exception as exc:
            traceback.print_exc()
            await channel.send(f"👋 Welcome {member.mention}!\n⚠️ Banner failed: {exc}")

async def setup(bot):
    await bot.add_cog(Welcome(bot))



