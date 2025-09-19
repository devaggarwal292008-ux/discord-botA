import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Prefix ping command
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! 🏓 {round(self.bot.latency * 1000)}ms")

    # Slash ping command
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Pong! 🏓 {round(self.bot.latency * 1000)}ms"
        )

async def setup(bot):
    await bot.add_cog(Utility(bot))


