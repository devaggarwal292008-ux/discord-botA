import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

DATA_FILE = "warnings.json"
LOG_CHANNEL_NAME = "📁｜mod-logs"  # Channel where actions are logged

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings: dict[int, int] = {}
        self.banned_words = [
            # English
            "fuck", "shit", "bitch", "asshole", "bastard", "slut", "dick", "pussy",
            "cock", "bollocks", "wanker", "motherfucker", "jerk", "douche",
            # Hindi
            "randi", "madarchod", "bhenchod", "lund", "chutiya", "gandu",
            "haraami", "gaand", "tatti", "kamina", "nalayak"
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

    # === Role Check ===
    def is_sentinel(self, interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.user.roles, name="🛡️ Void Sentinels")
        return role is not None

    # === Logging helper ===
    async def log_action(self, guild: discord.Guild, message: str):
        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            try:
                await log_channel.send(message)
            except discord.Forbidden:
                pass

    # === Helper methods ===
    async def add_warning(self, member: discord.Member, reason: str, send_func):
        user_id = member.id
        self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
        count = self.warnings[user_id]
        self.save_data()

        await send_func(f"⚠️ {member.mention} has been warned! Reason: {reason} ({count}/4)")
        await self.log_action(member.guild, f"⚠️ {member} warned. Reason: {reason} ({count}/4)")

        if count >= 4:
            try:
                await member.ban(reason="Exceeded warning limit")
                await send_func(f"⛔ {member.mention} has been banned after 4 warnings.")
                await self.log_action(member.guild, f"⛔ {member} banned after 4 warnings.")
                # ✅ Reset warnings after ban
                self.warnings[user_id] = 0
                self.save_data()
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
            await self.log_action(member.guild, f"✅ Cleared all warnings for {member}.")
        else:
            await send_func(f"ℹ️ {member.mention} has no warnings.")

    # === Auto warnings for banned words ===
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        lower_msg = message.content.lower()
        if any(word in lower_msg for word in self.banned_words):
            try:
                await message.delete()  # 🚫 Delete the offending message
            except discord.Forbidden:
                pass

            # ⚠️ DM the offender
            try:
                await message.author.send(
                    f"⚠️ Your message in **{message.guild.name}** was deleted because it contained abusive language."
                )
            except discord.Forbidden:
                pass

            # Add a warning (visible in channel too)
            await self.add_warning(
                message.author,
                reason="Used abusive word",
                send_func=message.channel.send
            )

        # ✅ Ensure slash commands still work
        await self.bot.process_commands(message)

    # === Slash Commands ===
    @app_commands.command(name="warnings", description="Check how many warnings a user has")
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        await self.show_warnings(member, interaction.response.send_message)

    @app_commands.command(name="warn", description="Warn a user")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "No reason provided"):
        if not self.is_sentinel(interaction):
            return await interaction.response.send_message("❌ You don’t have permission to use this command.", ephemeral=True)

        await self.add_warning(member, reason, interaction.response.send_message)

    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    async def clearwarnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not self.is_sentinel(interaction):
            return await interaction.response.send_message("❌ You don’t have permission to use this command.", ephemeral=True)

        await self.clear_warnings(member, interaction.response.send_message)

    @app_commands.command(name="mute", description="Mute a user for a certain duration (e.g. 10s, 5m, 2h)")
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str):
        if not self.is_sentinel(interaction):
            return await interaction.response.send_message("❌ You don’t have permission to use this command.", ephemeral=True)

        # Parse duration
        time_multipliers = {"s": 1, "m": 60, "h": 3600}
        unit = duration[-1]
        if unit not in time_multipliers:
            return await interaction.response.send_message("❌ Invalid duration format. Use `10s`, `5m`, or `2h`.", ephemeral=True)
        try:
            seconds = int(duration[:-1]) * time_multipliers[unit]
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number in duration.", ephemeral=True)

        try:
            await member.edit(timeout=discord.utils.utcnow() + discord.timedelta(seconds=seconds))
            await interaction.response.send_message(f"🔇 {member.mention} has been muted for {duration}.")
            await self.log_action(interaction.guild, f"🔇 {member} muted for {duration}.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don’t have permission to mute this user.", ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute a user")
    async def unmute_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not self.is_sentinel(interaction):
            return await interaction.response.send_message("❌ You don’t have permission to use this command.", ephemeral=True)

        try:
            await member.edit(timeout=None)
            await interaction.response.send_message(f"🔊 {member.mention} has been unmuted.")
            await self.log_action(interaction.guild, f"🔊 {member} unmuted.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don’t have permission to unmute this user.", ephemeral=True)

# === Cog Setup ===
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))


