from dotenv import load_dotenv
import os
from management.shop import Shop
from data.user import User
from colorizer.colorizer import Colorizer
from linker import linker
import discord
from discord.ext import commands
from discord.commands import Option
from discord.ui import Button, Select, View


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
    await ctx.defer()
    user_ = User()
    user_.load(user.id)
    if linker.needicon:
        hostguild = bot.get_guild(linker.hostguildid)
        mojis = hostguild.emojis
        for moji in mojis:
            if moji.id == linker.emojiid:
                emoji = str(moji)
    embed = discord.Embed(title=f"{user.name}'s balance", description=f"Balance: {user_.balance} {emoji if linker.needicon else ''}")
    await ctx.respond(embed=embed)

class ShopLRView(View):
    def __init__(self, ctx, embed, list_):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.embed = embed
        self.list = list_
        self.page = 0
        keys_list = list(list_.keys())
        self.pages = [{key: list_[key] for key in keys_list[i:i+5]} for i in range(0, len(keys_list), 5)]  # Convert dictionary into a list of sub-dictionaries
        user = User()
        user.load(ctx.author.id)
        self.user = user
        self.inventory = user.inventory

    async def pre_rendder(self):
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            if item in self.inventory:
                addedtext = f" (You already own {self.inventory[item]})"
            else:
                addedtext = ""
            self.embed.add_field(name=f"{item} | Price: {self.list[item]['price']}", value=self.list[item]['desc'] + addedtext, inline=False)
        return self.embed
    
    # Adds ⬅️ Left and Right ➡️ buttons to the view, all items are split into pages of 5
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def left(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Each item is shown in a field rendered as "name | price: price" with the description as the value
        self.page -= 1
        if self.page < 0:
            self.page = len(self.pages) - 1
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            if item in self.inventory:
                addedtext = f" (You already own {self.inventory[item]})"
            else:
                addedtext = ""
            self.embed.add_field(name=f"{item} | Price: {self.list[item]['price']}", value=self.list[item]['desc'] + addedtext, inline=False)
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def right(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        if self.page >= len(self.pages):
            self.page = 0
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            if item in self.inventory:
                addedtext = f" (You already own {self.inventory[item]})"
            else:
                addedtext = ""
            self.embed.add_field(name=f"{item} | Price: {self.list[item]['price']}", value=self.list[item]['desc'] + addedtext, inline=False)
        await interaction.response.edit_message(embed=self.embed, view=self)


    

@bot.slash_command(name="shop", description="View the shop")
async def shop_(ctx):
    await ctx.defer()
    embed = discord.Embed(title="Shop", description="Here's what's in the shop!")
    itemlist = shop.get_raw()
    lrv = ShopLRView(ctx, embed, itemlist)
    await lrv.pre_rendder()
    await ctx.respond(embed=embed, view=lrv)


bot.run(TOKEN)