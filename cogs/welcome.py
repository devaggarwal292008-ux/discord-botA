import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import os
import traceback

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _draw_gradient_text(self, base_img, position, text, font, gradient_colors):
        """Draw text with a left-to-right gradient (white -> cyan)."""
        # Make mask for the text
        mask = Image.new("L", base_img.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.text(position, text, font=font, fill=255)

        # Create gradient image
        gradient = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw_grad = ImageDraw.Draw(gradient)

        x, y = position
        text_width, text_height = font.getsize(text)
        for i in range(text_width):
            ratio = i / text_width
            r = int(gradient_colors[0][0] * (1 - ratio) + gradient_colors[1][0] * ratio)
            g = int(gradient_colors[0][1] * (1 - ratio) + gradient_colors[1][1] * ratio)
            b = int(gradient_colors[0][2] * (1 - ratio) + gradient_colors[1][2] * ratio)
            draw_grad.line([(x + i, y), (x + i, y + text_height)], fill=(r, g, b), width=1)

        # Paste gradient only where text mask is
        base_img.paste(gradient, (0, 0), mask)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            channel = member.guild.system_channel

        try:
            # Banner path
            banner_path = os.path.join(os.path.dirname(__file__), "..", "BANNER2.jpg")
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
            avatar = avatar.resize((220, 220))

            mask = Image.new("L", avatar.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

            avatar_x = 40
            avatar_y = (H - avatar.size[1]) // 2
            background.paste(avatar, (avatar_x, avatar_y), mask)

            # Fonts
            font_path = os.path.join(os.path.dirname(__file__), "..", "Asgrike.otf")
            try:
                font_big = ImageFont.truetype(font_path, 70)
                font_small = ImageFont.truetype(font_path, 40)
            except Exception:
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw = ImageDraw.Draw(background)

            text = f"HEY @{member.name.upper()} WELCOME TO {member.guild.name.upper()}"
            subtext = f"YOU ARE OUR {len(member.guild.members)}TH MEMBER!"

            # Text positions
            text_x = avatar_x + avatar.size[0] + 40
            text_y = avatar_y + 10
            subtext_x = text_x
            subtext_y = text_y + 80

            # Gradient text (big)
            self._draw_gradient_text(
                background,
                (text_x, text_y),
                text,
                font_big,
                ((255, 255, 255), (0, 255, 255))  # white → cyan
            )

            # Subtext (solid white)
            draw.text((subtext_x, subtext_y), subtext, font=font_small, fill="white")

            # Save & send
            buffer = io.BytesIO()
            background.save(buffer, "PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="welcome.png")
            if channel:
                await channel.send(content=f"🎉 Welcome to **{member.guild.name}** {member.mention}!", file=file)

        except Exception as exc:
            traceback.print_exc()
            if channel:
                await channel.send(
                    f"🎉 Welcome to **{member.guild.name}** {member.mention}!\n⚠️ (welcome image failed: {exc})"
                )

async def setup(bot):
    await bot.add_cog(Welcome(bot))




