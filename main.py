import discord
from discord.ext import commands
import os
import threading
from flask import Flask

# ===== Flask keep-alive =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# ===== Discord Bot Setup =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

async def load_cogs():
    for ext in ["cogs.utility", "cogs.levels", "cogs.moderation", "cogs.welcome"]:
        try:
            await bot.load_extension(ext)
            print(f"Loaded {ext}")
        except Exception as e:
            print(f"⚠️ Failed to load {ext}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

import asyncio
asyncio.run(main())

