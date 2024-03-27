from dotenv import load_dotenv
import os
from management.shop import Shop
from data.user import User
import discord
from discord.ext import commands
from discord.commands import Option


load_dotenv()
TOKEN = os.getenv("TOKEN")

shop = Shop()
shop.process()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"Successfully logged in as {bot.user}")
    

bot.run(TOKEN)