import discord
from discord.ext import commands
import math
from datetime import datetime, timedelta
import json
import os

DATA_FILE = "levels.json"

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_xp = {}
        self.last_daily = {}
        self.user_roles = {}  # ⬅️ track roles given
        self.level_roles = {
            5: "Novice Voidwalker",
            10: "Abyssal Explorer",
            20: "Eclipse Seeker",
            30: "Celestial Adept",
            50: "Void Master",
            75: "Eternal Shadow",
            100: "Abyssal Lord",
            150: "Cosmic Overlord"
        }
        self.load_data()

    # 📌 JSON persistence
    def save_data(self):
        data = {
            "user_xp": self.user_xp,
            "last_daily": {str(k): v.isoformat() for k, v in self.last_daily.items()},
            "user_roles": {str(k): v for k, v in self.user_roles.items()},
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.user_xp = {int(k): v for k, v in data.get("user_xp", {}).items()}
                self.last_daily = {
                    int(k): datetime.fromisoformat(v)
                    for k, v in data.get("last_daily", {}).items()
                }
                self.user_roles = {int(k): v for k, v in data.get("user_roles", {}).items()}

    # 📌 Leveling system
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = message.author.id
        self.user_xp[user_id] = self.user_xp.get(user_id, 0) + 10
        self.save_data()

        new_level = int(math.sqrt(self.user_xp[user_id]) // 2)
        current_level = getattr(message.author, "level", 0)

        if new_level > current_level:
            setattr(message.author, "level", new_level)
            await message.channel.send(f"🎉 {message.author.mention} leveled up to **Level {new_level}**!")

            if new_level in self.level_roles:
                role_name = self.level_roles[new_level]
                role = discord.utils.get(message.guild.roles, name=role_name)
                if not role:
                    role = await message.guild.create_role(
                        name=role_name,
                        color=discord.Color.purple(),
                        reason=f"Created for level {new_level}"
                    )

                # ✅ Only add role if not already saved
                given_roles = self.user_roles.get(user_id, [])
                if role_name not in given_roles:
                    await message.author.add_roles(role)
                    given_roles.append(role_name)
                    self.user_roles[user_id] = given_roles
                    self.save_data()
                    await message.channel.send(f"🏅 {message.author.mention} earned **{role_name}**!")

    # 📌 Rank (prefix + slash)
    @commands.command(aliases=["rank"])
    async def level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await self.send_level_embed(ctx, member)

    @commands.slash_command(name="level", description="Check your current level, XP, and roles")
    async def level_slash(self, ctx: discord.ApplicationContext, member: discord.Member = None):
        member = member or ctx.author
        await self.send_level_embed(ctx, member, slash=True)

    async def send_level_embed(self, ctx, member, slash=False):
        xp = self.user_xp.get(member.id, 0)
        lvl = int(math.sqrt(xp) // 2)
        next_level_xp = ((lvl + 1) * 2) ** 2
        progress = min(xp / next_level_xp, 1)
        progress_bar = "█" * int(progress * 20) + "─" * (20 - int(progress * 20))

        earned_roles = self.user_roles.get(member.id, [])
        roles_display = ", ".join(earned_roles) if earned_roles else "None"

        embed = discord.Embed(
            title=f"{member.display_name}'s Level Progress",
            color=discord.Color.green()
        )
        embed.add_field(name="Level", value=lvl, inline=True)
        embed.add_field(name="XP", value=f"{xp}/{next_level_xp}", inline=True)
        embed.add_field(name="Progress", value=f"[{progress_bar}]", inline=False)
        embed.add_field(name="Roles Earned", value=roles_display, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)

        if slash:
            await ctx.respond(embed=embed)
        else:
            await ctx.send(embed=embed)

    # 📌 Leaderboard
    @commands.command()
    async def leaderboard(self, ctx):
        if not self.user_xp:
            return await ctx.send("⚠️ No XP data yet!")

        sorted_users = sorted(self.user_xp.items(), key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="🏆 Leaderboard - Top Voidwalkers", color=discord.Color.gold())
        for i, (user_id, xp) in enumerate(sorted_users, start=1):
            member = ctx.guild.get_member(user_id)
            if member:
                lvl = int(math.sqrt(xp) // 2)
                embed.add_field(name=f"{i}. {member.display_name}", value=f"Level {lvl} | {xp} XP", inline=False)

        await ctx.send(embed=embed)

    # 📌 Daily reward
    @commands.command()
    async def daily(self, ctx):
        await self.handle_daily(ctx)

    @commands.slash_command(name="daily", description="Claim your daily XP reward")
    async def daily_slash(self, ctx: discord.ApplicationContext):
        await self.handle_daily(ctx, slash=True)

    async def handle_daily(self, ctx, slash=False):
        user_id = ctx.author.id
        now = datetime.utcnow()

        if user_id in self.last_daily and now < self.last_daily[user_id] + timedelta(hours=24):
            remaining = self.last_daily[user_id] + timedelta(hours=24) - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            msg = f"⏳ {ctx.author.mention}, you can claim daily again in **{hours}h {minutes}m**."
        else:
            self.user_xp[user_id] = self.user_xp.get(user_id, 0) + 50
            self.last_daily[user_id] = now
            self.save_data()
            msg = f"🎁 {ctx.author.mention}, you claimed your daily reward of **50 XP**!"

        if slash:
            await ctx.respond(msg)
        else:
            await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Levels(bot))

