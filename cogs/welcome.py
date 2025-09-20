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

        try:
            # --- Load banner (fallback to plain embed if not found) ---
            banner_path = os.path.join(os.path.dirname(__file__), "..", "banner.jpeg")
            if not os.path.exists(banner_path):
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

            # Center avatar
            avatar_x = (W - avatar.size[0]) // 2
            avatar_y = 60
            background.paste(avatar, (avatar_x, avatar_y), mask)

            # --- Draw text ---
            draw = ImageDraw.Draw(background)

            font_path = os.path.join(os.path.dirname(__file__), "..", "Poppins-Bold.ttf")
            try:
                font_big = ImageFont.truetype(font_path, 70)
                font_small = ImageFont.truetype(font_path, 45)
            except:
                font_big = ImageFont.load_default()
                font_small = ImageFont.load_default()

            text = f"Welcome {member.name}!"
            subtext = f"You are member #{len(member.guild.members)}"

            w1, h1 = draw.textsize(text, font=font_big)
            w2, h2 = draw.textsize(subtext, font=font_small)

            text_x = (W - w1) // 2
            subtext_x = (W - w2) // 2
            text_y = avatar_y + avatar.size[1] + 40
            subtext_y = text_y + h1 + 20

            # Shadow + text
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
            await channel.send(content=f"🎉 Welcome to **{member.guild.name}** {member.mention}!", file=file)

        except Exception as e:
            # If anything goes wrong, at least send a plain fallback message
            await channel.send(f"🎉 Welcome to **{member.guild.name}** {member.mention}!\n⚠️ (Error: {e})")

async def setup(bot):
    await bot.add_cog(Welcome(bot))







