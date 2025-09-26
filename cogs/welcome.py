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
        """Robust text measurement across Pillow versions."""
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
        """Find or create the channel named exactly '🚪｜welcome'. Try sensible fallbacks."""
        target_name = "🚪｜welcome"

        # 1) exact match
        ch = discord.utils.get(guild.text_channels, name=target_name)
        if ch:
            return ch

        # 2) any channel containing 'welcome'
        for c in guild.text_channels:
            if "welcome" in c.name.lower():
                return c

        # 3) try to create the exact channel (if bot has Manage Channels)
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            ch = await guild.create_text_channel(target_name, overwrites=overwrites)
            return ch
        except Exception:
            # can't create, fall back
            pass

        # 4) system channel if usable
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            return guild.system_channel

        # 5) first channel where bot can send
        for c in guild.text_channels:
            perms = c.permissions_for(guild.me)
            if perms.send_messages and perms.embed_links:
                return c

        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = await self._get_welcome_channel(guild)

        # Always ensure we at least send a fallback text if banner creation fails.
        if not channel:
            # attempt system channel then give up
            try:
                if guild.system_channel:
                    await guild.system_channel.send(f"🎉 Welcome to **{guild.name}** {member.mention}!")
            except Exception:
                pass
            return

        try:
            # BANNER2.jpeg expected in repo root (one level above cogs/)
            banner_path = os.path.join(os.path.dirname(__file__), "..", "BANNER2.jpeg")
            if not os.path.exists(banner_path):
                # fallback: send simple text
                await channel.send(f"🎉 Welcome to **{guild.name}** {member.mention}!")
                return

            # open banner
            background = Image.open(banner_path).convert("RGBA")
            W, H = background.size

            # download avatar bytes
            avatar_asset = member.display_avatar.replace(size=512)
            avatar_bytes = await avatar_asset.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

            # compute avatar size relative to banner height (keeps layout consistent)
            avatar_size = max(140, int(H * 0.38))  # example: ~38% of height, min 140
            avatar = ImageOps.fit(avatar, (avatar_size, avatar_size), Image.LANCZOS)

            # circular mask for avatar
            mask = Image.new("L", avatar.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

            # create bordered avatar (white ring)
            border_px = max(6, int(avatar.size[0] * 0.035))  # 3.5% of avatar width
            bordered_w = avatar.size[0] + border_px * 2
            bordered_h = avatar.size[1] + border_px * 2
            bordered_avatar = Image.new("RGBA", (bordered_w, bordered_h), (0, 0, 0, 0))

            # draw white circle for border
            border_mask = Image.new("L", (bordered_w, bordered_h), 0)
            bd = ImageDraw.Draw(border_mask)
            bd.ellipse((0, 0, bordered_w, bordered_h), fill=255)
            # inner hole
            bd.ellipse((border_px, border_px, bordered_w - border_px, bordered_h - border_px), fill=0)
            # paste white ring
            white_ring = Image.new("RGBA", (bordered_w, bordered_h), (255, 255, 255, 255))
            bordered_avatar.paste(white_ring, (0, 0), border_mask)
            # paste avatar onto ring
            bordered_avatar.paste(avatar, (border_px, border_px), mask)

            # paste bordered avatar onto banner (left area)
            avatar_x = int(W * 0.08)  # 8% from left
            avatar_y = int((H - bordered_h) // 2)
            background.paste(bordered_avatar, (avatar_x, avatar_y), bordered_avatar)

            # prepare fonts (scale based on banner height)
            font_path = os.path.join(os.path.dirname(__file__), "..", "Poppins-Bold.ttf")
            big_size = min(160, max(36, int(H * 0.14)))   # cap to 160px
            small_size = min(96, max(18, int(H * 0.07)))  # cap to 96px
            try:
                font_big = ImageFont.truetype(font_path, big_size)
                font_small = ImageFont.truetype(font_path, small_size)
            except Exception:
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw = ImageDraw.Draw(background)

            # texts
            display_name = member.display_name
            welcome_text = f"Welcome {display_name}!"
            member_count_text = f"You are member #{len(guild.members)}"

            # measure sizes
            w1, h1 = self._measure_text(draw, welcome_text, font_big)
            w2, h2 = self._measure_text(draw, member_count_text, font_small)

            # text x position to the right of avatar
            text_x = avatar_x + bordered_w + int(W * 0.06)  # spacing after avatar
            # compute vertical center for text block (align vertically with avatar)
            block_h = h1 + h2 + int(h1 * 0.25)
            text_y = avatar_y + (bordered_h - block_h) // 2

            # shadow + white text for readability
            shadow = max(2, int(big_size * 0.04))
            draw.text((text_x + shadow, text_y + shadow), welcome_text, font=font_big, fill="black")
            draw.text((text_x, text_y), welcome_text, font=font_big, fill="white")

            draw.text((text_x + shadow, text_y + h1 + int(h1 * 0.12) + shadow), member_count_text, font=font_small, fill="black")
            draw.text((text_x, text_y + h1 + int(h1 * 0.12)), member_count_text, font=font_small, fill="white")

            # save to buffer
            buffer = io.BytesIO()
            background.save(buffer, "PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="welcome.png")
            await channel.send(content=f"🎉 Welcome to **{guild.name}**, {member.mention}!", file=file)

        except Exception as exc:
            # log to console for debugging, but still send fallback
            traceback.print_exc()
            try:
                await channel.send(f"🎉 Welcome to **{guild.name}** {member.mention}!\n⚠️ (welcome image failed)")
            except Exception:
                # last resort: try system channel
                try:
                    if guild.system_channel:
                        await guild.system_channel.send(f"🎉 Welcome to **{guild.name}** {member.mention}!")
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(Welcome(bot))











