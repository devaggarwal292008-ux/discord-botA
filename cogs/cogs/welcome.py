import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Find welcome channel
        channel = discord.utils.get(member.guild.text_channels, name="🚪｜welcome")
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(send_messages=True, view_channel=True)
            }
            channel = await member.guild.create_text_channel("🚪｜welcome", overwrites=overwrites)

        # Embed welcome message
        embed = discord.Embed(
            title="🎉 Welcome to Transcending Void!",
            description=f"Hello {member.mention}, prepare to journey into the Void. "
                        "Join our tournaments and enjoy your stay!",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{len(member.guild.members)} joined!")

        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
