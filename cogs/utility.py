import discord
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Prefix ping
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"🏓 Pong! Latency: {round(self.bot.latency * 1000)}ms")

    # Slash ping
    @commands.slash_command(name="ping", description="Check the bot's latency")
    async def ping_slash(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"🏓 Pong! Latency: {round(self.bot.latency * 1000)}ms")

    # Custom help
    @commands.command()
    async def help(self, ctx):
        await self.send_help_embed(ctx)

    @commands.slash_command(name="help", description="Show bot commands")
    async def help_slash(self, ctx: discord.ApplicationContext):
        await self.send_help_embed(ctx, slash=True)

    async def send_help_embed(self, ctx, slash=False):
        embed = discord.Embed(
            title="📖 Transcending Void - Bot Commands",
            description="Here are my available commands:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🎮 Levels", value="`!level`/`/level`, `!rank`, `!leaderboard`, `!daily`/`/daily`", inline=False)
        embed.add_field(name="🛡 Moderation", value="`!warn` (auto warns on abuse)", inline=False)
        embed.add_field(name="⚙️ Utility", value="`!ping`/`/ping`, `!help`/`/help`", inline=False)
        embed.set_footer(text="Voidwalker Bot - Organized for tournaments & fun 🌌")

        if slash:
            await ctx.respond(embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
