import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}
        self.banned_words = [
            "fuck", "shit", "bitch", "asshole",
            "randi", "madarchod", "bhenchod", "lund"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        lower_msg = message.content.lower()
        if any(word in lower_msg for word in self.banned_words):
            user_id = message.author.id
            self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
            count = self.warnings[user_id]

            await message.channel.send(f"⚠️ {message.author.mention}, you have been warned! ({count}/4)")

            if count >= 4:
                try:
                    await message.author.ban(reason="Exceeded warning limit for abusive words.")
                    await message.channel.send(f"⛔ {message.author.mention} has been banned for repeated abuse.")
                except discord.Forbidden:
                    await message.channel.send("❌ I don’t have permission to ban this user.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        user_id = member.id
        self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
        count = self.warnings[user_id]

        await ctx.send(f"⚠️ {member.mention} has been warned! Reason: {reason} ({count}/4)")

        if count >= 4:
            try:
                await member.ban(reason="Exceeded warning limit")
                await ctx.send(f"⛔ {member.mention} has been banned after 4 warnings.")
            except discord.Forbidden:
                await ctx.send("❌ I don’t have permission to ban this user.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
