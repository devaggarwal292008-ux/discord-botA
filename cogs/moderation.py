import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
import re

DATA_FILE = "warnings.json"

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings: dict[int, int] = {}
        self.banned_words = [
            # English
            "fuck", "shit", "bitch", "asshole", "bastard", "cunt", "dick", "pussy", "slut", "whore",
            # Hindi
            "randi", "madarchod", "bhenchod", "lund", "chutiya", "gaand", "harami", "nalayak",
            "kamina", "kutta", "kutti", "gandu", "tatti"
        ]
        # compile regex for performance, word boundaries + case insensitive
        self.banned_regex = re.compile(r"\b(" + "|".join(map(re.escape, self.banned_words)) + r")\b", re.IGNORECASE)
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

    # === Logging helper ===
    async def log_action(self, guild: discord.Guild, message: str):
        log_channel = discord.utils.get(guild.text_channels, name="📁｜mod-logs")
        if log_channel:
            await log_channel.send(message)

    # === Helper: check moderator role ===
    async def is_moderator(self, interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.user.roles, name="｜Void Sentinels")
        return role is not None

    # === Helper methods (shared) ===
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
                # reset warnings after ban
                self.warnings.pop(user_id, None)
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
            await self.log_action(member.guild, f"✅ Cleared warnings for {member}")
        else:
            await send_func(f"ℹ️ {member.mention} has no warnings.")

    # === Auto warnings for banned words ===
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check message for banned words using regex
        if self.banned_regex.search(message.content):
            try:
                await message.delete()
            except discord.Forbidden:
                await self.log_action(
                    message.guild,
                    f"⚠️ Could not delete message from {message.author} (missing permissions)."
                )

            try:
                await message.author.send(
                    f"⚠️ Your message in **{message.guild.name}** was deleted because it contained abusive language."
                )
            except discord.Forbidden:
                pass

            await self.add_warning(
                message.author,
                reason="Used abusive word",
                send_func=message.channel.send
            )

        await self.bot.process_commands(message)

    # === Slash commands ===
    @app_commands.command(name="warnings", description="Check how many warnings a user has")
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        await self.show_warnings(member, interaction.response.send_message)

    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    async def clearwarnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.is_moderator(interaction):
            return await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)
        await self.clear_warnings(member, interaction.response.send_message)

    @app_commands.command(name="warn", description="Warn a user")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "No reason provided"):
        if not await self.is_moderator(interaction):
            return await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)
        await self.add_warning(member, reason, interaction.response.send_message)

    @app_commands.command(name="mute", description="Mute a user for a certain duration")
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        if not await self.is_moderator(interaction):
            return await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)

        await interaction.response.defer(thinking=True)

        seconds = self.parse_duration(duration)
        if seconds is None:
            return await interaction.followup.send("❌ Invalid duration format. Use s/m/h/d (e.g., 10m, 2h).")

        try:
            until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
            await member.timeout(until, reason=reason)
            await interaction.followup.send(f"🔇 {member.mention} has been muted for {duration}. Reason: {reason}")
            await self.log_action(interaction.guild, f"🔇 {member} muted for {duration}. Reason: {reason}")
        except discord.Forbidden:
            await interaction.followup.send("❌ I don’t have permission to mute this user.")

    @app_commands.command(name="unmute", description="Unmute a user")
    async def unmute_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.is_moderator(interaction):
            return await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)

        await interaction.response.defer(thinking=True)

        try:
            await member.timeout(None)
            await interaction.followup.send(f"🔊 {member.mention} has been unmuted.")
            await self.log_action(interaction.guild, f"🔊 {member} unmuted.")
        except discord.Forbidden:
            await interaction.followup.send("❌ I don’t have permission to unmute this user.")

    # === Duration parser ===
    def parse_duration(self, duration: str):
        try:
            unit = duration[-1]
            value = int(duration[:-1])
            if unit == "s":
                return value
            elif unit == "m":
                return value * 60
            elif unit == "h":
                return value * 3600
            elif unit == "d":
                return value * 86400
        except:
            return None

# === Cog Setup ===
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
