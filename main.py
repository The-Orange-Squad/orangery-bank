from dotenv import load_dotenv
import os
from management.shop import Shop
from data.user import User
import discord
from discord.ext import commands
from discord.commands import Option

shop = Shop()
shop.process()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

load_dotenv()

TOKEN = os.getenv("TOKEN")

bot.run(TOKEN)