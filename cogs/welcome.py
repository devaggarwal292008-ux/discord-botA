import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import traceback

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_welcome_channel(self, guild: discord.Guild):
        ch = discord.utils.get(guild.text_channels, name="🚪｜welcome")
        if ch:
            return ch
        for c in guild.text_channels:
            if "welcome" in c.name.lower():
                return c
        return guild.system_channel

    def _measure_text(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
        """Return (w,h) for text using a safe method across Pillow versions."""
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except Exception:
            try:
                return draw.textsize(text, font=font)
            except Exception:
                try:
                    return font.getmask(text).size
                except Exception:
                    return (len(text) * 10, 20)

    def _draw_gradient_text(self, base_img: Image.Image, pos: tuple[int, int], text: str, font: ImageFont.ImageFont, left_color: tuple, right_color: tuple, shadow: int = 2):
        """
        Draw left-to-right gradient text onto base_img at pos.
        - Uses a mask sized to the text then pastes a per-pixel gradient.
        - Draws a subtle shadow behind the text first for readability.
        """
        draw_base = ImageDraw.Draw(base_img)

        # measure text size
        w, h = self._measure_text(draw_base, text, font)

        if w <= 0 or h <= 0:
            return

        x, y = pos

        # draw shadow (solid black) behind where gradient will be placed
        if shadow:
            draw_base.text((x + shadow, y + shadow), text, font=font, fill="black")

        # create mask for text (text drawn at (0,0) in mask coordinates)
        mask = Image.new("L", (w, h), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.text((0, 0), text, font=font, fill=255)

        # build gradient image of size (w,h)
        grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        grad_draw = ImageDraw.Draw(grad)
        for i in range(w):
            t = i / (w - 1) if w > 1 else 0
            r = int(left_color[0] * (1 - t) + right_color[0] * t)
            g = int(left_color[1] * (1 - t) + right_color[1] * t)
            b = int(left_color[2] * (1 - t) + right_color[2] * t)
            grad_draw.line([(i, 0), (i, h)], fill=(r, g, b, 255))

        # paste gradient onto base image using the text mask
        base_img.paste(grad, (x, y), mask)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = await self._get_welcome_channel(guild)
        if not channel:
            print(f"[WELCOME] No welcome channel found for guild {guild.name}")
            return

        try:
            # project root (one level up from cogs/)
            base_dir = os.path.dirname(os.path.dirname(__file__))
            banner_path = os.path.join(base_dir, "BANNER2.jpg")
            font_path = os.path.join(base_dir, "Asgrike.otf")  # your requested font

            if not os.path.exists(banner_path):
                print(f"[WELCOME] Banner missing at {banner_path}")
                await channel.send(f"🎉 Welcome {member.mention}! (Banner not found)")
                return

            background = Image.open(banner_path).convert("RGBA")
            W, H = background.size
            print(f"[WELCOME] Loaded banner {W}x{H}")

            # load avatar
            avatar_asset = member.display_avatar.replace(size=256)
            avatar_bytes = await avatar_asset.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

            # avatar size relative to banner height
            avatar_size = int(H * 0.6)
            avatar = ImageOps.fit(avatar, (avatar_size, avatar_size), Image.LANCZOS)

            # circular mask + white ring
            mask = Image.new("L", avatar.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)

            border = max(4, int(H * 0.02))
            bordered = Image.new("RGBA", (avatar_size + 2 * border, avatar_size + 2 * border), (0, 0, 0, 0))
            ring = ImageDraw.Draw(bordered)
            ring.ellipse((0, 0, bordered.size[0] - 1, bordered.size[1] - 1), fill=(255, 255, 255, 255))
            bordered.paste(avatar, (border, border), mask)

            avatar_x = int(W * 0.04)
            avatar_y = (H - bordered.size[1]) // 2
            background.paste(bordered, (avatar_x, avatar_y), bordered)

            # fonts (sizes scaled by banner height)
            try:
                font_big = ImageFont.truetype(font_path, int(H * 0.14))   # main text ≈ 14% of height
                font_small = ImageFont.truetype(font_path, int(H * 0.07)) # subtext ≈ 7% of height
                print("[WELCOME] Loaded Asgrike.otf")
            except Exception as e:
                print(f"[WELCOME] Font load failed: {e} (using fallback)")
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw = ImageDraw.Draw(background)

            # build texts
            main_name = member.display_name.upper()
            # keep line length reasonable: don't let guild name + name overflow uncontrollably
            guild_name = guild.name.upper()
            text = f"HEY @{main_name} WELCOME TO {guild_name}"
            subtext = f"YOU ARE OUR {len(guild.members)}TH MEMBER!"

            # positions
            text_x = avatar_x + bordered.size[0] + int(W * 0.05)
            # vertically center main text with avatar
            text_w, text_h = self._measure_text(draw, text, font_big)
            avatar_center_y = avatar_y + bordered.size[1] // 2
            text_y = avatar_center_y - text_h // 2 - int(H * 0.04)  # slight upward offset for style
            subtext_y = text_y + text_h + int(H * 0.03)

            # draw gradient main text (white -> cyan)
            self._draw_gradient_text(
                background,
                (text_x, text_y),
                text,
                font_big,
                left_color=(255, 255, 255),
                right_color=(0, 220, 220),
                shadow=3
            )

            # draw subtext with shadow + solid white
            shadow = 2
            draw.text((text_x + shadow, subtext_y + shadow), subtext, font=font_small, fill="black")
            draw.text((text_x, subtext_y), subtext, font=font_small, fill="white")

            # save to buffer and send
            buf = io.BytesIO()
            background.save(buf, "PNG")
            buf.seek(0)
            file = discord.File(fp=buf, filename="welcome.png")
            await channel.send(content=f"🎉 Welcome to **{guild.name}** {member.mention}!", file=file)
            print(f"[WELCOME] Sent banner for {member.display_name}")

        except Exception as exc:
            traceback.print_exc()
            await channel.send(f"👋 Welcome {member.mention}!\n⚠️ (banner failed: {exc})")

async def setup(bot):
    await bot.add_cog(Welcome(bot))





