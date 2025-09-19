import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# ------------------- KEEP ALIVE SERVER -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------------------------

# Start keep-alive server so Render + UptimeRobot keep it alive
keep_alive()

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup (disable default help)
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔗 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Slash sync failed: {e}")

    # Load cogs
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"🔹 Loaded cog {filename}")
            except Exception as cog_error:
                print(f"⚠️ Failed to load {filename}: {cog_error}")

bot.run(TOKEN)
