from dotenv import load_dotenv
import os
from management.shop import Shop
from data.user import User
from colorizer.colorizer import Colorizer
from linker import linker
import discord
from discord.ext import commands
from discord.commands import Option


load_dotenv()
TOKEN = os.getenv("TOKEN")

shop = Shop()
shop.process()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

colorizer = Colorizer()

@bot.event
async def on_ready():
    print(colorizer.colorize("Logged in as", "green") + " " + bot.user.name)
    print(colorizer.colorize("Connected to the following guilds: ", "yellow"))
    for guilds in bot.guilds:
        print(guilds.name + " | " + colorizer.colorize(str(guilds.id), "cyan"))
    
@bot.slash_command(name="balance", description="Check the balance of the specified user")
async def balance(ctx, user: Option(User, "The user to check the balance of", required=True)):
    user_ = User()
    user_.load(user.id)
    embed = discord.Embed(title=f"{user.mention}'s balance", description=f"Balance: {user.balance}")
    await ctx.send(embed=embed)


bot.run(TOKEN)