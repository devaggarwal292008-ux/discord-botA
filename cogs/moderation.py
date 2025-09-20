import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
import datetime

DATA_FILE = "warnings.json"


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings: dict[int, int] = {}

        # 🚫 Extended list of banned words (English + Hindi)
        self.banned_words = [
            # English
            "fuck", "shit", "bitch", "asshole", "bastard", "slut",
            "whore", "dick", "pussy", "cunt", "cock", "dumbass",
            "motherfucker", "fucker", "retard", "gayfuck", "jerk",

            # Hindi (Romanized abusive terms)
            "randi", "madarchod", "bhenchod", "lund", "chutiya",
            "chut", "gandu", "gaand", "harami", "nalayak", "bevakoof",
            "suar", "kutta", "kutiya", "kamina", "jhantu", "tatti",
            "bhosdike", "rakhail", "kameena", "faltu", "gaandmasti",
        ]

        self.load_data()

    # === JSON persistence ===
    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.warnings, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.warnings = {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, ValueError):
                self.warnings = {}

    # === Slash-safe send function ===
    async def send_slash(self, interaction: discord.Interaction, content: str):
        if not interaction.response.is_done():
            await interaction.response.send_message(content)
        else:
            await interaction.followup.send(content)

    # === Role check helper ===
    def has_void_sentinel(self, interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.user.roles, name="🛡️ Void Sentinels")
        return role is not None

    # === Helper methods ===
    async def add_warning(self, member: discord.Member, reason: str, interaction: discord.Interaction = None, channel=None):
        user_id = member.id
        self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
        count = self.warnings[user_id]
        self.save_data()

        msg = f"⚠️ {member.mention} has been warned! Reason: {reason} ({count}/4)"
        if interaction:
            await self.send_slash(interaction, msg)
        elif channel:
            await channel.send(msg)

        # Try to DM the user
        try:
            await member.send(f"You have been warned in {member.guild.name}: {reason} ({count}/4)")
        except discord.Forbidden:
            pass

        if count >= 4:
            try:
                await member.ban(reason="Exceeded warning limit")
                ban_msg = f"⛔ {member.mention} has been banned after 4 warnings."
                if interaction:
                    await self.send_slash(interaction, ban_msg)
                elif channel:
                    await channel.send(ban_msg)
            except discord.Forbidden:
                err_msg = "❌ I don’t have permission to ban this user."
                if interaction:
                    await self.send_slash(interaction, err_msg)
                elif channel:
                    await channel.send(err_msg)

    async def show_warnings(self, member: discord.Member, interaction: discord.Interaction):
        count = self.warnings.get(member.id, 0)
        await self.send_slash(interaction, f"📊 {member.mention} has **{count} warnings**.")

    async def clear_warnings(self, member: discord.Member, interaction: discord.Interaction):
        if member.id in self.warnings:
            self.warnings.pop(member.id)
            self.save_data()
            await self.send_slash(interaction, f"✅ Cleared all warnings for {member.mention}.")
        else:
            await self.send_slash(interaction, f"ℹ️ {member.mention} has no warnings.")

    # === Auto warnings for banned words ===
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        lower_msg = message.content.lower()
        if any(re.search(rf"\b{word}\b", lower_msg) for word in self.banned_words):
            await self.add_warning(
                message.author,
                reason="Used abusive word",
                channel=message.channel
            )

    # === Slash: Check warnings ===
    @app_commands.command(name="warnings", description="Check how many warnings a user has")
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        await self.show_warnings(member, interaction)

    # === Slash: Clear warnings ===
    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    async def clearwarnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not self.has_void_sentinel(interaction):
            await self.send_slash(interaction, "❌ You don’t have permission to use this command.")
            return
        await self.clear_warnings(member, interaction)

    # === Slash: Manual warn ===
    @app_commands.command(name="warn", description="Warn a user manually")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not self.has_void_sentinel(interaction):
            await self.send_slash(interaction, "❌ You don’t have permission to use this command.")
            return
        await self.add_warning(member, reason, interaction=interaction)

    # === Slash: Mute ===
    @app_commands.command(name="mute", description="Mute a user for a given time (e.g. 10m, 2h, 1d)")
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason provided"):
        if not self.has_void_sentinel(interaction):
            await self.send_slash(interaction, "❌ You don’t have permission to use this command.")
            return

        time_multipliers = {"m": 60, "h": 3600, "d": 86400}
        seconds = 0
        try:
            unit = duration[-1]
            value = int(duration[:-1])
            if unit in time_multipliers:
                seconds = value * time_multipliers[unit]
            else:
                await self.send_slash(interaction, "❌ Invalid time format. Use `m`, `h`, or `d` (e.g. 10m, 2h, 1d).")
                return
        except (ValueError, IndexError):
            await self.send_slash(interaction, "❌ Invalid time format. Example: `/mute @user 10m reason`")
            return

        until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)

        try:
            await member.timeout(until, reason=reason)
            await self.send_slash(interaction, f"🔇 {member.mention} has been muted for {duration}. Reason: {reason}")
        except discord.Forbidden:
            await self.send_slash(interaction, "❌ I don’t have permission to mute this user.")

    # === Slash: Unmute ===
    @app_commands.command(name="unmute", description="Unmute a user immediately")
    async def unmute_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not self.has_void_sentinel(interaction):
            await self.send_slash(interaction, "❌ You don’t have permission to use this command.")
            return

        try:
            await member.timeout(None)  # Removes timeout
            await self.send_slash(interaction, f"🔊 {member.mention} has been unmuted.")
        except discord.Forbidden:
            await self.send_slash(interaction, "❌ I don’t have permission to unmute this user.")


# === Cog Setup ===
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
