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

        # Load banner
        banner_path = os.path.join(os.path.dirname(__file__), "..", "banner.jpeg")
        if not os.path.exists(banner_path):
            await channel.send("⚠️ Banner image not found! Please upload `banner.jpeg` in the bot folder.")
            return

        background = Image.open(banner_path).convert("RGBA")
        W, H = background.size  # Banner dimensions

        # Get member avatar
        avatar_asset = member.display_avatar.replace(size=256)
        avatar_bytes = await avatar_asset.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((200, 200))

        # Circle mask for avatar
        mask = Image.new("L", avatar.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

        # Position avatar centered at top
        avatar_x = (W - avatar.size[0]) // 2
        avatar_y = 60
        background.paste(avatar, (avatar_x, avatar_y), mask)

        # Draw text
        draw = ImageDraw.Draw(background)

        # Load font (Poppins-Bold if available)
        font_path = os.path.join(os.path.dirname(__file__), "..", "Poppins-Bold.ttf")
        try:
            font_big = ImageFont.truetype(font_path, 70)
            font_small = ImageFont.truetype(font_path, 45)
        except:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()

        text = f"Welcome {member.name}!"
        subtext = f"You are member #{len(member.guild.members)}"

        # Measure text sizes for centering
        w1, h1 = draw.textsize(text, font=font_big)
        w2, h2 = draw.textsize(subtext, font=font_small)

        text_x = (W - w1) // 2
        subtext_x = (W - w2) // 2
        text_y = avatar_y + avatar.size[1] + 40
        subtext_y = text_y + h1 + 20

        # Draw text (white with black shadow for readability)
        shadow_offset = 3
        draw.text((text_x + shadow_offset, text_y + shadow_offset), text, font=font_big, fill="black")
        draw.text((text_x, text_y), text, font=font_big, fill="white")

        draw.text((subtext_x + shadow_offset, subtext_y + shadow_offset), subtext, font=font_small, fill="black")
        draw.text((subtext_x, subtext_y), subtext, font=font_small, fill="white")

        # Save to buffer
        buffer = io.BytesIO()
        background.save(buffer, "PNG")
        buffer.seek(0)

        # Send banner
        file = discord.File(fp=buffer, filename="welcome.png")
        await channel.send(content=f"🎉 Welcome to **{member.guild.name}** {member.mention}!", file=file)

async def setup(bot):
    await bot.add_cog(Welcome(bot))






