import discord
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Ping command (prefix)
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! 🏓 {round(self.bot.latency * 1000)}ms")

    # Ping command (slash)
    @commands.slash_command(name="ping", description="Check bot latency")
    async def ping_slash(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Pong! 🏓 {round(self.bot.latency * 1000)}ms")

async def setup(bot):
    await bot.add_cog(Utility(bot))

