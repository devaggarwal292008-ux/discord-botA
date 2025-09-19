import os
import threading
import asyncio
from flask import Flask
import discord
from discord.ext import commands

# ===== Flask keep-alive =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# ===== Discord Bot Setup =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Use bot.tree instead of creating a new one ---
tree = bot.tree   # ✅ FIXED

@bot.event
async def on_ready():
    # Sync slash commands each time the bot starts
    await tree.sync()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

async def load_cogs():
    """Load all cog extensions."""
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

if __name__ == "__main__":
    asyncio.run(main())



