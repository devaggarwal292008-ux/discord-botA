import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "warnings.json"

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings: dict[int, int] = {}
        self.banned_words = [
            "fuck", "shit", "bitch", "asshole",
            "randi", "madarchod", "bhenchod", "lund"
        ]
        self.load_data()

    # === JSON persistence ===
    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.warnings, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.warnings = {int(k): v for k, v in data.items()}

    # === Helper methods (shared by prefix + slash) ===
    async def add_warning(self, member: discord.Member, reason: str, send_func):
        user_id = member.id
        self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
        count = self.warnings[user_id]
        self.save_data()

        await send_func(f"⚠️ {member.mention} has been warned! Reason: {reason} ({count}/4)")

        if count >= 4:
            try:
                await member.ban(reason="Exceeded warning limit")
                await send_func(f"⛔ {member.mention} has been banned after 4 warnings.")
            except discord.Forbidden:
                await send_func("❌ I don’t have permission to ban this user.")

    async def show_warnings(self, member: discord.Member, send_func):
        count = self.warnings.get(member.id, 0)
        await send_func(f"📊 {member.mention} has **{count} warnings**.")

    async def clear_warnings(self, member: discord.Member, send_func):
        if member.id in self.warnings:
            self.warnings.pop(member.id)
            self.save_data()
            await send_func(f"✅ Cleared all warnings for {member.mention}.")
        else:
            await send_func(f"ℹ️ {member.mention} has no warnings.")

    # === Auto warnings for banned words ===
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        lower_msg = message.content.lower()
        if any(word in lower_msg for word in self.banned_words):
            await self.add_warning(
                message.author,
                reason="Used abusive word",
                send_func=message.channel.send
            )

        # ✅ Make sure prefix commands still run
        await self.bot.process_commands(message)

    # === Manual warn (prefix) ===
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason="No reason provided"):
        await self.add_warning(member, reason, ctx.send)

    # === Check warnings (prefix) ===
    @commands.command()
    async def warnings(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        await self.show_warnings(member, ctx.send)

    # === Check warnings (slash) ===
    @app_commands.command(name="warnings", description="Check how many warnings a user has")
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        await self.show_warnings(member, interaction.response.send_message)

    # === Clear warnings (prefix) ===
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        await self.clear_warnings(member, ctx.send)

    # === Clear warnings (slash) ===
    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    @commands.has_permissions(kick_members=True)
    async def clearwarnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        await self.clear_warnings(member, interaction.response.send_message)

# === Cog Setup ===
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
