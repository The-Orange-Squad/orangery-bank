from dotenv import load_dotenv
import os
from management.shop import Shop
from management.modlist import GuildSetup
from data.user import User
from colorizer.colorizer import Colorizer
from linker import linker
import discord
import discord.utils
from discord.ext import commands
from discord.commands import Option
from discord.ui import Button, Select, View
from messagecounter.msgc import LastMessage
from management.rewardroles import RewardRoles
import random
import asyncio


load_dotenv()
TOKEN = os.getenv("TOKEN")

shop = Shop()
shop.process()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

colorizer = Colorizer()
LastMessage = LastMessage()
LastMessage.load()

rr = RewardRoles()
rr.load()

def execute_func_with_string(func_str, parameters):
    func_name, params = func_str.split('(')
    params = params.rstrip(')')
    param_values = []
    
    if params.strip() != "":
        param_names = params.split(',')
        for param_name in param_names:
            param_name = param_name.strip()
            if param_name in parameters:
                param_values.append(parameters[param_name])
            else:
                raise ValueError(f"Parameter '{param_name}' not found in the current context.")
    
    if func_name.strip() in globals():
        func = globals()[func_name.strip()]
        func(*param_values)
    else:
        raise ValueError(f"Function '{func_name.strip()}' not found in the global context.")

def constructCurrName(withemoji=True):
    if linker.needicon:
        hostguild = bot.get_guild(linker.hostguildid)
        mojis = hostguild.emojis
        for moji in mojis:
            if moji.id == linker.emojiid:
                emoji = str(moji)
        return f"{linker.currname} {emoji}" if withemoji else linker.currname
    return linker.currname

@bot.event
async def on_ready():
    print(colorizer.colorize("Logged in as", "green") + " " + bot.user.name)
    print(colorizer.colorize("Connected to the following guilds: ", "yellow"))
    for guilds in bot.guilds:
        print(guilds.name + " | " + colorizer.colorize(str(guilds.id), "cyan"))
    
@bot.slash_command(name="balance", description="Check the balance of the specified user")
async def balance(ctx, user: Option(User, "The user to check the balance of", required=False) = None):
    if user == None:
        user = ctx.author
    await ctx.defer()
    user_ = User()
    user_.load(user.id)
    # Check if the author is a user of the bot and check if the author is banned
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    embed = discord.Embed(title=f"{user.name}'s balance", description=f"Balance: {user_.get_balance(ctx.guild.id)} {constructCurrName()}", color=discord.Color.random())
    await ctx.respond(embed=embed)

class ShopLRView(View):
    def __init__(self, ctx, embed, list_, guildid):
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
        self.inventory = user.get_inventory(guildid)

    async def pre_rendder(self):
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            item = shop.process_single(item)
            if item in self.inventory:
                addedtext = f" (You already own {self.inventory[item]})"
            else:
                addedtext = ""
            self.embed.add_field(name=f"{shop.pair(item)} ({shop.get_type(item)}) | Price: {self.list[shop.pair(item)]['price']}", value=self.list[shop.pair(item)]['desc'] + addedtext, inline=False)
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
            item = shop.process_single(item)
            if item in self.inventory:
                addedtext = f" (You already own {self.inventory[item]})"
            else:
                addedtext = ""
            self.embed.add_field(name=f"{shop.pair(item)} ({shop.get_type(item)}) | Price: {self.list[shop.pair(item)]['price']}", value=self.list[shop.pair(item)]['desc'] + addedtext, inline=False)
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def right(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        if self.page >= len(self.pages):
            self.page = 0
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            item = shop.process_single(item)
            if item in self.inventory:
                addedtext = f" (You already own {self.inventory[item]})"
            else:
                addedtext = ""
            self.embed.add_field(name=f"{shop.pair(item)} ({shop.get_type(item)}) | Price: {self.list[shop.pair(item)]['price']}", value=self.list[shop.pair(item)]['desc'] + addedtext, inline=False)
        await interaction.response.edit_message(embed=self.embed, view=self)


@bot.slash_command(name="shop", description="View the shop")
async def shop_(ctx):
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    await ctx.defer()
    embed = discord.Embed(title="Shop", description="Here's what's in the shop!")
    itemlist = shop.get_raw()
    lrv = ShopLRView(ctx, embed, itemlist, ctx.guild.id)
    await lrv.pre_rendder()
    await ctx.respond(embed=embed, view=lrv)

setupgroup = bot.create_group(name="setup", description="Setup the bot for your server")

@setupgroup.command(name="modrole", description="Set the moderator role for the server")
@commands.has_permissions(administrator=True)
async def modrole(ctx, role: discord.Role):
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    await ctx.defer()
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    setup.set(ctx.guild.id, "modrole", role.id)
    try:
        embed = discord.Embed(title="Success!", description=f"Set the moderator role to {role.mention}", color=discord.Color.green())
    except:
        embed = discord.Embed(title="Failed!", description="An error occurred while setting the moderator role", color=discord.Color.red())
        setup.set(ctx.guild.id, "modrole", "undefined")
    await ctx.respond(embed=embed)

@setupgroup.command(name="adminrole", description="Set the administrator role for the server")
@commands.has_permissions(administrator=True)
async def adminrole(ctx, role: discord.Role):
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    await ctx.defer()
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    setup.set(ctx.guild.id, "adminrole", role.id)
    try:
        embed = discord.Embed(title="Success!", description=f"Set the administrator role to {role.mention}", color=discord.Color.green())
    except:
        embed = discord.Embed(title="Failed!", description="An error occurred while setting the administrator role", color=discord.Color.red())
        setup.set(ctx.guild.id, "adminrole", "undefined")
    await ctx.respond(embed=embed)

@modrole.error
async def modrole_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="Error!", description="You need to have the administrator permission to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)

@adminrole.error
async def adminrole_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="Error!", description="You need to have the administrator permission to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
    
@setupgroup.command(name="give_money", description="Give money to a user")
async def give_money(ctx, user: discord.Member, amount: int):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["modrole"] not in [role.id for role in ctx.author.roles] and setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the moderator role or the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    user_ = User()
    user_.load(user.id)
    user_.edit_money(amount, ctx.guild.id)
    embed = discord.Embed(title="Success!", description=f"Gave {amount} {constructCurrName()} to {user.mention}", color=discord.Color.green())
    await ctx.respond(embed=embed)

async def shopAutoComplete(ctx: discord.AutocompleteContext):
    return shop.get_processed().keys()

@bot.slash_command(name="buy", description="Buy an item from the shop")
async def buy(ctx, item: Option(str, "The item to buy", required=True, autocomplete=discord.utils.basic_autocomplete(shopAutoComplete)), amount: Option(int, "The amount of the item to buy", required=False, default=1)):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    user = User()
    user.load(ctx.author.id)
    itemlist = shop.get_processed()
    if not shop.is_valid_item(item):
        embed = discord.Embed(title="Error!", description="Invalid item", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if user.get_balance(ctx.guild.id) < itemlist[item]["price"] * amount:
        embed = discord.Embed(title="Error!", description="You don't have enough money to buy this item", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    user.edit_money(-itemlist[item]["price"] * amount, ctx.guild.id)
    user.add_item(item, amount, ctx.guild.id)
    if linker.needicon:
        hostguild = bot.get_guild(linker.hostguildid)
        mojis = hostguild.emojis
        for moji in mojis:
            if moji.id == linker.emojiid:
                emoji = str(moji)
    embed = discord.Embed(title="Success!", description=f"Bought {amount} {shop.pair(item)} for {itemlist[item]['price'] * amount} {constructCurrName()}", color=discord.Color.green())
    await ctx.respond(embed=embed)

class invLRView(View):
    def __init__(self, ctx, embed, list_):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.embed = embed
        self.list = list_
        self.page = 0
        keys_list = list(list_.keys())
        self.pages = [{key: list_[key] for key in keys_list[i:i+5]} for i in range(0, len(keys_list), 5)]
        user = User()
        user.load(ctx.author.id)
        self.user = user

    async def pre_rendder(self):
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            self.embed.add_field(name=f"{shop.pair(item)} | Amount: {self.list[item]}", value=shop.get_desc(item), inline=False)
        return self.embed
    
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def left(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page -= 1
        if self.page < 0:
            self.page = len(self.pages) - 1
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            self.embed.add_field(name=f"{shop.pair(item)} | Amount: {self.list[item]}", value=shop.get_desc(item), inline=False)
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def right(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        if self.page >= len(self.pages):
            self.page = 0
        self.embed.clear_fields()
        for item in self.pages[self.page]:
            self.embed.add_field(name=f"{shop.pair(item)} | Amount: {self.list[item]}", value=shop.get_desc(item), inline=False)
        await interaction.response.edit_message(embed=self.embed, view=self)

@bot.slash_command(name="inventory", description="View the inventory of the specified user")
async def inventory(ctx, user: Option(User, "The user to check the inventory of", required=False) = None):
    if user == None:
        user = ctx.author
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    await ctx.defer()
    user_ = User()
    user_.load(user.id)
    if not user_.get_inventory(ctx.guild.id) or user_.get_inventory(ctx.guild.id) == {}:
        embed = discord.Embed(title="Error!", description="This user has no items in their inventory", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    embed = discord.Embed(title=f"{user.name}'s inventory", description="Here's what's in the inventory!")
    lrv = invLRView(ctx, embed, user_.get_inventory(ctx.guild.id))
    await lrv.pre_rendder()
    await ctx.respond(embed=embed, view=lrv)


@bot.slash_command(name="sell", description="Sell an item from the inventory")
async def sell(ctx, item: Option(str, "The item to sell", required=True, autocomplete=discord.utils.basic_autocomplete(shopAutoComplete)), amount: Option(int, "The amount of the item to sell", required=False, default=1)):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    user = User()
    user.load(ctx.author.id)
    itemlist = shop.get_processed()
    # The amount of money given for each item sold is randomized, it's between 50% and 150% of the item's price. If there is a modifier the user has, the amount of money given is multiplied by the modifier
    if not shop.is_valid_item(item):
        embed = discord.Embed(title="Error!", description="Invalid item", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if item not in user.inventory[ctx.guild.id]:
        embed = discord.Embed(title="Error!", description="You don't own this item", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    
    # ultramegacomplexedunintellegible code
    # ALBERT EINSTEIN WOULD BE PROUD
    price = itemlist[item]["price"]
    normalprice = price * amount
    pricelist = [random.randint(int(price * 0.5), int(price * 1.5)) for i in range(amount)]
    price = sum(pricelist)
    price = price * user.get_mod(ctx.guild.id)

    user.edit_money(price, ctx.guild.id)
    user.remove_item(item, amount, ctx.guild.id)

    embed = discord.Embed(title="Success!", description=f"Sold {amount} {shop.pair(item)} for {price} {constructCurrName()}", color=discord.Color.green())
    pricediff = price - normalprice
    abspricediff = abs(pricediff)
    # the price difference determines whether the user gets more or less money than the average price
    if pricediff > 0:
        temptext = "more than"
    elif pricediff < 0:
        temptext = "less than"
    else:
        temptext = "the same as"
    
    embed.set_footer(text=f"You sold this for {price} {linker.currname}, which is {str(abspricediff) + ' ' if temptext != 'the same as' else ''}{linker.currname + ' ' if temptext != 'the same as' else ''}{temptext} the average price")
    await ctx.respond(embed=embed)

def generatePB(curr, max):
    emojis = ("🟩", "⬛")
    pb = ""
    percentage = round((curr / max) * 100)
    for i in range(10):
        if i < percentage // 10:
            pb += emojis[0]
        else:
            pb += emojis[1]
    
    return pb

@bot.slash_command(name="rank", description="Check the rank of the specified user")
async def rank(ctx, user: Option(User, "The user to check the rank of", required=False), advanced: Option(bool, "Whether to show the rank in an advanced way", required=False, default=False)):
    await ctx.defer()
    if user is None:
        user = ctx.author
    
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    user_ = User()
    user_.load(user.id)
    
    if not advanced:
        embed = discord.Embed(
            title=f"{user.name}'s rank",
            description=f"Level: {user_.get_lvl(ctx.guild.id)}\nXP: {user_.get_xp(ctx.guild.id)} / {round(user_.getxpreq(user_.get_lvl(ctx.guild.id)))}\nMessage Count: {user_.get_msgc(ctx.guild.id)}",
            color=discord.Color.random()
        )
    else:
        embed = discord.Embed(title=f"Detailed Rank", description="See below for a detailed view of your rank")
        lvl = user_.get_lvl(ctx.guild.id)
        rr = RewardRoles()
        rr.load()
        try:
            rrlist = rr.roles[ctx.guild.id]
        except:
            rrlist = {}
        maxreward = max(rrlist.keys() or [0])
        
        next_reward_level = None
        for reward_level in sorted(rrlist.keys()):
            if lvl < reward_level:
                next_reward_level = reward_level
                break
        
        if next_reward_level is None and rrlist != {}:
            adata = f"\nYou have reached the maximum rewarded level for this server ({maxreward})"
        elif rrlist == {}:
            adata = "\nNo rewards have been set for this server"
        else:
            adata = f"\nNext Reward: Level {next_reward_level}\n\nProgress:\n {generatePB(lvl, next_reward_level)}"
        
        embed.add_field(name="Level", value=f"{lvl} {adata}", inline=False)
        
        xp = user_.get_xp(ctx.guild.id)
        embed.add_field(name="XP", value=f"{xp} / {round(user_.getxpreq(lvl))}\n\nProgress:\n{generatePB(xp, round(user_.getxpreq(lvl)))}", inline=False)
        
        msgc = user_.get_msgc(ctx.guild.id)
        embed.add_field(name="Message Count", value=f"{msgc}", inline=False)
        
        money = user_.get_balance(ctx.guild.id)
        embed.add_field(name="Money", value=f"{money} {constructCurrName()}\n\nCapacity Used:\n{generatePB(money, linker.m_maxmoney)}", inline=False)
    
    await ctx.respond(embed=embed)


@bot.slash_command(name='lvlreward', description='Set a role to be given to a user when they reach a certain level')
async def lvlreward(ctx, level: int, role: discord.Role):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    # Check if the user has the admin/mod role
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined" or setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role or administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["modrole"] not in [role.id for role in ctx.author.roles] and setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the moderator role or the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    rr.add(level, role.id, ctx.guild.id)
    embed = discord.Embed(title="Success!", description=f"Set the role {role.mention} to be given to users when they reach level {level}", color=discord.Color.green())
    await ctx.respond(embed=embed)

@bot.slash_command(name='lvlrewardremove', description='Remove a role that is given to a user when they reach a certain level')
async def lvlrewardremove(ctx, level: int):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined" or setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role or administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["modrole"] not in [role.id for role in ctx.author.roles] and setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the moderator role or the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    rr.remove(level, ctx.guild.id)
    embed = discord.Embed(title="Success!", description=f"Removed the role that is given to users when they reach level {level}", color=discord.Color.green())
    await ctx.respond(embed=embed)

@bot.slash_command(name='lvlrewards', description='View all the level rewards set for the server')
async def lvlrewards(ctx):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot\n\n", color=discord.Color.red())
    
    rrlist = rr.roles[ctx.guild.id]
    embed = discord.Embed(title="Level Rewards", description="Here are all the level rewards set for this server")
    for key, value in rrlist.items():
        embed.description += f"\n**Level {key}**:"
        try:
            embed.description += f" {discord.utils.get(ctx.guild.roles, id=value).mention}"
        except:
            embed.description += f" Could not retrieve role (ID: {value})"
    
    embed.set_footer(text=f"For reaching a new level, you also receive from {linker.rewardrange[0]} to {linker.rewardrange[1]} {linker.currname}, multiplied by your level and then divided by 2")
    await ctx.respond(embed=embed)


@bot.slash_command(name='ban', description='Ban a user from using the bot', guilds=[linker.hostguildid])
async def ban(ctx, user: discord.Member):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    if not author.pos == "owner":
        embed = discord.Embed(title="Error!", description="You need to be the owner of the bot to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    user_ = User()
    user_.load(user.id)
    user_.ban()
    if user_.banned:
        embed = discord.Embed(title="Success!", description=f"Banned {user.mention} from using the bot", color=discord.Color.green())
    else:
        embed = discord.Embed(title="Failed!", description="An error occurred while banning the user", color=discord.Color.red())
    await ctx.respond(embed=embed)

@bot.slash_command(name='unban', description='Unban a user from using the bot', guilds=[linker.hostguildid])
async def unban(ctx, user: discord.Member):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    if not author.pos == "owner":
        embed = discord.Embed(title="Error!", description="You need to be the owner of the bot to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    user_ = User()
    user_.load(user.id)
    user_.unban()
    if not user_.banned:
        embed = discord.Embed(title="Success!", description=f"Unbanned {user.mention} from using the bot", color=discord.Color.green())
    else:
        embed = discord.Embed(title="Failed!", description="An error occurred while unbanning the user", color=discord.Color.red())
    await ctx.respond(embed=embed)

@bot.slash_command(name='coinflip', description='Flip a coin')
async def coinflip(ctx, bet: int, side: Option(str, "The side to bet on", required=True, choices=["Heads", "Tails"])):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    user = User()
    user.load(ctx.author.id)
    if user.get_balance(ctx.guild.id) < bet:
        embed = discord.Embed(title="Error!", description="You don't have enough money to bet this amount", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if bet < 1:
        embed = discord.Embed(title="Error!", description="You can't bet less than 1", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    user.edit_money(-bet, ctx.guild.id)
    result = random.choice(["Heads", "Tails"])
    if result == side:
        user.edit_money(bet * 2, ctx.guild.id)
        embed = discord.Embed(title="Success!", description=f"The coin landed on {result}! You won {bet} {constructCurrName()}", color=discord.Color.green())
    else:
        embed = discord.Embed(title="Failure!", description=f"The coin landed on {result}! You lost {bet} {constructCurrName()}", color=discord.Color.red())
    await ctx.respond(embed=embed)

@bot.slash_command(name='dice', description='Roll a dice')
async def dice(ctx, bet: int, number: Option(int, "The number to bet on", required=True)):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    user = User()
    user.load(ctx.author.id)
    if user.get_balance(ctx.guild.id) < bet:
        embed = discord.Embed(title="Error!", description="You don't have enough money to bet this amount", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if bet < 6:
        embed = discord.Embed(title="Error!", description="You can't bet less than 6", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if number not in range(1, 7):
        embed = discord.Embed(title="Error!", description="You can only bet on numbers between 1 and 6", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    results = []
    for i in range(6):
        results.append(random.randint(1, 6))
    
    results_str = []
    for i in results:
        if i == number:
            results_str.append('win')
        else:
            results_str.append('lose')
    
    outcome = 0
    for i in results_str:
        if i == 'win':
            outcome += 1
    
    # the result is based off the outcome
    # if the outcome is positive, the user wins
    # if the outcome is negative, the user loses
    # if the outcome is 0, the user gets their money back
    user.edit_money(-bet, ctx.guild.id)
    if outcome > 0:
        reward = 0
        for i in results_str:
            if i == 'win':
                reward += bet / 6
        user.edit_money(round(reward * 2), ctx.guild.id)
        # show all results
        embed = discord.Embed(title="Success!", description=f"The dice landed on {results[0]}, {results[1]}, {results[2]}, {results[3]}, {results[4]}, {results[5]}! You won {round(reward)} {constructCurrName()}", color=discord.Color.green())
    elif outcome <= 0:
        embed = discord.Embed(title="Failure!", description=f"The dice landed on {results[0]}, {results[1]}, {results[2]}, {results[3]}, {results[4]}, {results[5]}! You lost {bet} {constructCurrName()}", color=discord.Color.red())
    await ctx.respond(embed=embed)

@bot.slash_command(name='slots', description='Play the slots')
async def slots(ctx, bet: int):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    user = User()
    user.load(ctx.author.id)
    if user.get_balance(ctx.guild.id) < bet:
        embed = discord.Embed(title="Error!", description="You don't have enough money to bet this amount", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if bet < 1:
        embed = discord.Embed(title="Error!", description="You can't bet less than 1", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    user.edit_money(-bet, ctx.guild.id)
    embed = discord.Embed(title="The slots are spinning...", description="Good luck!")
    msg = await ctx.respond(embed=embed)
    await asyncio.sleep(1)
    pool = ["🍒", "🍋", "🍊", "7️⃣", "🪙", "💎", "♥️", "♠️", "🔔", "🍇", "🍓", "🍉"]
    for i in range(5):
        results = []
        for i in range(3):
            results.append(random.choice(pool))
        
        embed.description = f"Spinning... \n\n{results[0]} {results[1]} {results[2]}"
        await msg.edit(embed=embed)
        await asyncio.sleep(0.5)
    
    # calculate the win amount
    # each emoji is 0.4x the bet
    # if all emojis are the same, the win amount is 2x the bet
    # if two emojis are the same, the win amount is 1.5x the bet
    # if all emojis are different, the win amount is 0
    if results[0] == results[1] == results[2]:
        win = round(bet * 10)
    elif results[0] == results[1] or results[0] == results[2] or results[1] == results[2]:
        win = bet
    elif results[0] != results[1] != results[2]:
        win = 0

    user.edit_money(win, ctx.guild.id)
    if win > 0 and win > bet:
        embed.title = "Success!"
        embed.description = f"{results[0]} {results[1]} {results[2]}\n\nYou won {win} {constructCurrName()}!"
        embed.color = discord.Color.green()
    elif win == bet:
        embed.title = "You didn't win, but at least you got your money back!"
        embed.description = f"{results[0]} {results[1]} {results[2]}\n\nYou got your {bet} {constructCurrName()} back!"
        embed.color = discord.Color.gold()
    else:
        embed.title = "Failure!"
        embed.description = f"{results[0]} {results[1]} {results[2]}\n\nYou lost {bet} {constructCurrName()}"
        embed.color = discord.Color.red()
    
    await msg.edit(embed=embed)

@bot.user_command(name="View Balance", description="View the balance of the specified user")
async def view_balance(ctx, user: discord.User):
    user_ = User()
    user_.load(user.id)
    embed = discord.Embed(title=f"{user.name}'s balance", description=f"Balance: {user_.get_balance(ctx.guild.id)} {constructCurrName()}", color=discord.Color.random())
    await ctx.respond(embed=embed)

@bot.user_command(name="View Rank", description="View the rank of the specified user")
async def view_rank(ctx, user: discord.User):
    user_ = User()
    user_.load(user.id)
    embed = discord.Embed(title=f"{user.name}'s rank", description=f"Level: {user_.get_lvl(ctx.guild.id)}\nXP: {user_.get_xp(ctx.guild.id)} / {round(user_.getxpreq(user_.get_lvl(ctx.guild.id)))}\nMessage Count: {user_.get_msgc(ctx.guild.id)}", color=discord.Color.random())
    await ctx.respond(embed=embed)

@bot.user_command(name="View Inventory", description="View the inventory of the specified user")
async def view_inventory(ctx, user: discord.User):
    user_ = User()
    user_.load(user.id)
    embed = discord.Embed(title=f"{user.name}'s inventory", description="Here's what's in the inventory!")
    lrv = invLRView(ctx, embed, user_.get_inventory(ctx.guild.id))
    await lrv.pre_rendder()
    await ctx.respond(embed=embed, view=lrv)

@bot.slash_command(name="leaderboard", description="View the leaderboard of the server")
async def leaderboard(ctx, option: Option(str, "The leaderboard option", required=False, choices=["balance", "level"], default="balance")):
    # This takes a while to load, so we defer the response
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    servermembers = [member.id for member in ctx.guild.members]
    templb = {}
    filelist = os.listdir("data/users")
    filelist.remove("basehandler.json")
    for user in filelist:
        user_ = User()
        id = int(user.replace(".json", ""))
        # check if the user is in the guild
        if not id in servermembers:
            continue
        user_.load(id)
        if option == "balance":
            templb[user_.get_balance(ctx.guild.id)] = id
        elif option == "level":
            templb[user_.get_lvl(ctx.guild.id)] = id
    if option == "balance":
        lb = dict(sorted(templb.items(), reverse=True))
        embed = discord.Embed(title=f"{ctx.guild.name}'s Balance Leaderboard", description="Here are the top 10 users in the server based on balance")
    elif option == "level":
        lb = dict(sorted(templb.items(), key=lambda x: x[0], reverse=True))
        embed = discord.Embed(title=f"{ctx.guild.name}'s Level Leaderboard", description="Here are the top 10 users in the server based on level")
    i = 0
    for key, value in lb.items():
        if i == 10:
            break
        user = bot.get_user(value)
        if option == "balance":
            embed.add_field(name=f"{user.name}", value=f"Balance: {key} {constructCurrName()}", inline=False)
        elif option == "level":
            embed.add_field(name=f"{user.name}", value=f"Level: {key}", inline=False)
        i += 1
    await ctx.respond(embed=embed)


@bot.slash_command(name="work", description="Work to earn money")
@commands.cooldown(1, 43200, commands.BucketType.user)  # 12 hours cooldown
async def work(ctx):
    await ctx.defer()
    user = User()
    user.load(ctx.author.id)

    if user.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    reward = random.randint(linker.w_rewardrange[0], linker.w_rewardrange[1])
    reward *= user.getmodifiers(ctx.guild.id)

    user.edit_money(reward, ctx.guild.id)
    embed = discord.Embed(title="Success!", description=f"You worked and earned {reward} {constructCurrName()}", color=discord.Color.green())

    if random.random() < linker.w_xpchance:
        xp = random.randint(linker.w_xprewardrange[0], linker.w_xprewardrange[1])
        user.give_xp(xp, ctx.guild.id)
        embed.add_field(name="XP Reward (Bonus)", value=f"Received {xp} XP", inline=False)

    await ctx.respond(embed=embed)

@work.error
async def work_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title="Error!", description=f"You need to wait {error.retry_after} seconds before working again", color=discord.Color.red())
        await ctx.respond(embed=embed)
    

@bot.slash_command(name="crime", description="Commit a crime to earn money (or fail and lose money)")
@commands.cooldown(1, 43200, commands.BucketType.user)  # 12 hours cooldown
async def crime(ctx, risk: Option(int, "The risk level of the crime.", required=True, choices=[1, 2, 3])):
    await ctx.defer()
    user = User()
    user.load(ctx.author.id)

    if user.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    roundedchance = round((linker.c_defwinchance / risk) * 100, 2)
    w_or_l = random.randint(1, 100)
    if linker.c_defwinchance / risk > w_or_l:
        reward = random.randint(linker.c_defwinreward[0], linker.c_defwinreward[1]) * risk
        reward *= user.getmodifiers(ctx.guild.id)
        user.edit_money(reward, ctx.guild.id)
        embed = discord.Embed(title="Success!", description=f"You committed a crime and earned {reward} {constructCurrName()}", color=discord.Color.green())
        embed.set_footer(text=f"This crime was a level {risk} crime, means that your chance of success was {roundedchance}%")
    else:
        # c_deflosspenalty is used to calculate the amount of money you lose from your total balance
        loss = round(user.get_balance(ctx.guild.id) * linker.c_deflosspenalty)
        user.edit_money(-loss, ctx.guild.id)
        embed = discord.Embed(title="Failure!", description=f"You committed a crime and lost {loss} {constructCurrName()}", color=discord.Color.red())
        embed.set_footer(text=f"This crime was a level {risk} crime, means that your chance of success was {roundedchance}%")
    
    await ctx.respond(embed=embed)

@crime.error
async def crime_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title="Error!", description=f"You need to wait {error.retry_after} seconds before committing a crime again", color=discord.Color.red())
        await ctx.respond(embed=embed)
    
@bot.slash_command(name="daily", description="Claim your daily reward")
@commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hours cooldown
async def daily(ctx):
    await ctx.defer()
    user = User()
    user.load(ctx.author.id)

    if user.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    reward = random.randint(linker.dailyreward[0], linker.dailyreward[1])
    reward *= user.getmodifiers(ctx.guild.id)
    user.edit_money(reward, ctx.guild.id)
    embed = discord.Embed(title="Success!", description=f"Claimed your daily reward and received {reward} {constructCurrName()}", color=discord.Color.green())
    await ctx.respond(embed=embed)


@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        # in hours
        embed = discord.Embed(title="Error!", description=f"You can only claim your daily reward daily (self-explanatory). Please wait {round(error.retry_after / 3600)} hours before claiming it again", color=discord.Color.red())
        await ctx.respond(embed=embed)
    

def open_giftbox(ctx):
    print(colorizer.colorize("Opening gift box...", "yellow"))
    user = User()
    user.load(ctx.author.id)
    print(colorizer.colorize(f"User {ctx.author.id} loaded", "green"))
    if user.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        return embed
    # get random item from shop
    itemlist = shop.get_processed()
    item = random.choice(list(itemlist.keys()))
    print(colorizer.colorize(f"Received {item} from the gift box", "green"))
    amount = 1
    user.add_item(item, amount, ctx.guild.id)
    embed = discord.Embed(title="Success!", description=f"Opened the gift box and received {amount} {shop.pair(item)}", color=discord.Color.green())
    return embed

def eat(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        return embed
    eatcommentlist = ["That was tasty, wasn't it?", "Yum!", "Delicious!", "Satisfying 😌", "Well, that was a good meal!"]
    embed = discord.Embed(title="Eaten!", description=random.choice(eatcommentlist), color=discord.Color.green())
    return embed

def open_mbox(ctx):
    outcomes = 10

    user = User()
    user.load(ctx.author.id)

    outcome = random.randint(1, outcomes)
    # outcome 1: get a basic reward (m_basicreward)
    # outcome 2: get some items from the m_bitempool
    # outcome 3: get the same item (m_mboxid)
    # outcome 4: get a little bit of XP
    # outcome 5: get m_basicreward * 2
    # NEGATIVE
    # outcome 6: lose 1 of a random item you have
    # outcome 7: lose m_basicreward * 1.4
    # outcome 8: lose a little bit of XP
    # outcome 9: lose a random item you have (completely)
    # outcome 10: lose m_basicreward * 2

    if outcome == 1:
        reward = random.randint(linker.m_basicreward[0], linker.m_basicreward[1])
        reward *= user.getmodifiers(ctx.guild.id)
        user.edit_money(reward, ctx.guild.id)
        embed = discord.Embed(title="There was some money!", description=f"Opened the mystery box and received {reward} {constructCurrName()}", color=discord.Color.green())
    elif outcome == 2:
        # the m_bitempool is a range of two ids, between which the item id will be chosen
        item = random.randint(linker.m_bitempool[0], linker.m_bitempool[1])
        amount = random.randint(1, 5)
        # find the item name
        itemname = shop.get_processed().get(item)["name"]
        user.add_item(itemname, amount, ctx.guild.id)
        embed = discord.Embed(title="There were some items!", description=f"Opened the mystery box and received {amount} {shop.pair(itemname)}", color=discord.Color.green())
    elif outcome == 3:
        item = linker.m_mboxid
        item = shop.get_processed().get(item)["name"]
        user.add_item(item, 1, ctx.guild.id)
        embed = discord.Embed(title="There was... another mystery box?", description=f"Surprisingly, you found another mystery box inside the mystery box! Seems like another chance?", color=discord.Color.green())
    elif outcome == 4:
        xp = random.randint(30, 50)
        user.give_xp(xp, ctx.guild.id)
        embed = discord.Embed(title="There was some XP!", description=f"Opened the mystery box and received {xp} XP", color=discord.Color.green())
    elif outcome == 5:
        reward = random.randint(linker.m_basicreward[0], linker.m_basicreward[1]) * 2
        reward *= user.getmodifiers(ctx.guild.id)
        user.edit_money(reward, ctx.guild.id)
        embed = discord.Embed(title="There was a lot of money!", description=f"Opened the mystery box and received {reward} {constructCurrName()}", color=discord.Color.green())
    elif outcome == 6:
        item = random.choice(list(user.inventory[ctx.guild.id].keys()))
        user.remove_item(item, 1, ctx.guild.id)
        embed = discord.Embed(title="There was a thief!", description=f"Opened the mystery box and lost 1 {shop.pair(item)}", color=discord.Color.red())
    elif outcome == 7:
        loss = round(linker.m_basicreward[0] * 1.4)
        user.edit_money(-loss, ctx.guild.id)
        embed = discord.Embed(title="There was a thief!", description=f"Opened the mystery box and lost {loss} {constructCurrName()}", color=discord.Color.red())
    elif outcome == 8:
        xp = random.randint(10, 20)
        user.give_xp(-xp, ctx.guild.id)
        embed = discord.Embed(title="There was a thief!", description=f"Opened the mystery box and lost {xp} XP", color=discord.Color.red())
    elif outcome == 9:
        item = random.choice(list(user.inventory[ctx.guild.id].keys()))
        user.remove_item(item, user.inventory[ctx.guild.id][item], ctx.guild.id)
        embed = discord.Embed(title="There was a thief!", description=f"Opened the mystery box and lost all {shop.pair(item)}", color=discord.Color.red())
    elif outcome == 10:
        loss = round(linker.m_basicreward[0] * 2)
        user.edit_money(-loss, ctx.guild.id)
        embed = discord.Embed(title="There was a thief!", description=f"Opened the mystery box and lost {loss} {constructCurrName()}", color=discord.Color.red())
    return embed

def read_book(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        return embed
    xp = random.randint(linker.w_rewardrange[0], linker.w_rewardrange[1])
    newlvl = user.give_xp(xp * user.get_mod(ctx.guild.id), ctx.guild.id)
    embed = discord.Embed(title="Read a book!", description=f"Read a book and received {xp} XP", color=discord.Color.green())
    if newlvl == "newlvl":
        embed.add_field(name="Level Up!", value=f"You leveled up to level {user.get_lvl(ctx.guild.id)}!", inline=False)
    return embed


def go_fishing(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        return discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    
    fish_types = ["🐟 Common Fish", "🐠 Tropical Fish", "🦈 Shark", "🐡 Pufferfish", "🦑 Squid"]
    caught = random.choice(fish_types)
    value = random.randint(50, 500)
    
    user.add_item(caught, 1, ctx.guild.id)
    user.edit_money(value, ctx.guild.id)
    
    embed = discord.Embed(title="Gone Fishing!", description=f"You caught a {caught} and sold it for {value} {constructCurrName()}!", color=discord.Color.blue())
    return embed

def go_mining(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        return discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    
    minerals = ["💎 Diamond", "🥇 Gold Nugget", "🥈 Silver Ore", "🔷 Sapphire", "♦️ Ruby"]
    mined = random.choice(minerals)
    value = random.randint(100, 1000)
    
    user.add_item(mined, 1, ctx.guild.id)
    user.edit_money(value, ctx.guild.id)
    
    embed = discord.Embed(title="Mining Adventure!", description=f"You mined a {mined} and sold it for {value} {constructCurrName()}!", color=discord.Color.dark_gray())
    return embed

def plant_magic_seeds(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        return discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    
    outcomes = [
        ("🌳 Money Tree", f"grew into a Money Tree! You harvested {random.randint(300, 1000)} {constructCurrName()}!"),
        ("🌻 XP Flower", f"blossomed into an XP Flower! You gained {random.randint(100, 500)} XP!"),
        ("🍄 Wisdom Mushroom", "turned into a Wisdom Mushroom! Your next adventure will be extra rewarding!"),
        ("🌵 Thorny Cactus", "became a Thorny Cactus. Ouch! You lost a small amount of money tending to it.")
    ]
    
    result, description = random.choice(outcomes)
    
    if "Money Tree" in result:
        value = int(description.split()[-2])
        user.edit_money(value, ctx.guild.id)
    elif "XP Flower" in result:
        xp = int(description.split()[-3])
        user.give_xp(xp, ctx.guild.id)
    elif "Thorny Cactus" in result:
        loss = random.randint(50, 200)
        user.edit_money(-loss, ctx.guild.id)
        description += f" (-{loss} {constructCurrName()})"
    
    embed = discord.Embed(title="Magic Seeds Planted!", description=f"Your magic seeds {description}", color=discord.Color.green())
    return embed

def use_crystal_ball(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        return discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    
    futures = [
        "You will come into great fortune soon.",
        "A challenging adventure awaits you.",
        "An unexpected friend will become very important.",
        "Your next big decision will lead to success.",
        "A small mistake will lead to a big opportunity."
    ]
    
    prediction = random.choice(futures)
    bonus = random.randint(50, 200)
    user.edit_money(bonus, ctx.guild.id)
    
    embed = discord.Embed(title="Crystal Ball Prediction", description=f"The crystal ball shows: {prediction}\nFor this glimpse into the future, you've been awarded {bonus} {constructCurrName()}!", color=discord.Color.purple())
    return embed

def perform_alchemy(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        return discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    
    experiments = [
        ("🧪 Health Potion", "restores vitality", 300),
        ("💨 Invisibility Powder", "grants stealth", 500),
        ("🔥 Fire Resistance Elixir", "protects from flames", 400),
        ("⚡ Lightning in a Bottle", "harnesses electricity", 600),
        ("🌈 Prismatic Dye", "changes colors magically", 250)
    ]
    
    result, effect, value = random.choice(experiments)
    user.add_item(result, 1, ctx.guild.id)
    user.edit_money(value, ctx.guild.id)
    
    embed = discord.Embed(title="Alchemy Experiment", description=f"You created {result} which {effect}!\nYou can sell this for {value} {constructCurrName()}.", color=discord.Color.gold())
    return embed

def use_disguise_kit(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        return discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    
    disguises = ["👑 Royalty", "🕵️ Secret Agent", "👨‍🍳 Master Chef", "🧙 Wizard", "🤖 Robot"]
    chosen = random.choice(disguises)
    bonus = random.randint(100, 500)
    user.edit_money(bonus, ctx.guild.id)
    
    embed = discord.Embed(title="Undercover Mission", description=f"You disguised yourself as {chosen} and completed a secret mission!\nReward: {bonus} {constructCurrName()}", color=discord.Color.teal())
    return embed

def use_lucky_ticket(ctx):
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        return discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    
    outcomes = [
        ("🎉 Jackpot", f"You won the jackpot! {random.randint(1000, 5000)} {constructCurrName()} have been added to your account!"),
        ("💰 Cash Prize", f"You won a cash prize of {random.randint(100, 999)} {constructCurrName()}!"),
        ("🎁 Mystery Box", "You won a Mystery Box!"),
        ("📚 XP Boost", f"You received an XP boost of {random.randint(50, 250)} XP!"),
        ("😢 No Luck", "Sorry, this ticket wasn't a winner. Better luck next time!")
    ]
    
    result, description = random.choice(outcomes)
    
    if "Jackpot" in result or "Cash Prize" in result:
        value = int(description.split()[-5])
        user.edit_money(value, ctx.guild.id)
    elif "Mystery Box" in result:
        user.add_item("Mystery Box", 1, ctx.guild.id)
    elif "XP Boost" in result:
        xp = int(description.split()[-3])
        user.give_xp(xp, ctx.guild.id)
    
    embed = discord.Embed(title="Lucky Ticket Result", description=description, color=discord.Color.gold())
    return embed


@bot.slash_command(name='use', description='Use an item from your inventory')
async def use(ctx, item: Option(str, "The item to use", required=True, autocomplete=discord.utils.basic_autocomplete(shopAutoComplete))):
    await ctx.defer()
    user = User()
    user.load(ctx.author.id)
    if user.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if item not in user.inventory[ctx.guild.id]:
        embed = discord.Embed(title="Error!", description="You don't own this item", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    itemlist = shop.get_processed()
    item_data = itemlist.get(item)
    if item_data and item_data.get("funcstr"):
        exec_globals = globals().copy()
        exec_globals.update({"ctx": ctx, "user": user, "item_data": item_data})
        try:
            returned = eval(item_data["funcstr"], exec_globals)
        except Exception as e:
            embed = discord.Embed(title="Error!", description=str(e), color=discord.Color.red())
            await ctx.respond(embed=embed)
            return
        user.refresh()
        user.remove_item(item, 1, ctx.guild.id)
        await ctx.respond(embed=returned)
    else:
        embed = discord.Embed(title="Error!", description="This item cannot be used", color=discord.Color.red())
        await ctx.respond(embed=embed)
    
@bot.slash_command(name='setup_givexp', description='Give XP to a user')
async def setup_givexp(ctx, user: discord.Member, xp: int):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined" or setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role or administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["modrole"] not in [role.id for role in ctx.author.roles] and setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the moderator role or the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    user_ = User()
    user_.load(user.id)
    returned = user_.give_xp(xp, ctx.guild.id)

    # give roles if the user has reached a new level
    if returned == "newlvl":
        embed = discord.Embed(title="Level Up!", description=f"{user.mention} has leveled up to level {user_.get_lvl(ctx.guild.id)}!", color=discord.Color.green())
        reward = round(user_.get_lvl(ctx.guild.id) * random.randint(linker.rewardrange[0], linker.rewardrange[1]) * (user_.get_mod(ctx.guild.id) / 2))
        reward *= user_.getmodifiers(ctx.guild.id)
        user_.edit_money(reward, ctx.guild.id)
        embed.add_field(name="Reward", value=f"Received {reward} {constructCurrName()}", inline=False)
        if rr.hasreward(user_.get_lvl(ctx.guild.id), ctx.guild.id):
            try:
                role = rr.get(user_.get_lvl(ctx.guild.id), ctx.guild.id)
                role = discord.utils.get(ctx.guild.roles, id=role)
                await user.add_roles(role)
                embed.add_field(name="Role Reward", value=f"Received the role {role.mention}", inline=False)
            except Exception as e:
                embed.add_field(name="Role Reward", value="Could not give the role", inline=False)
                embed.add_field(name="Error", value=str(e), inline=False)
        await ctx.respond(embed=embed)

    embed = discord.Embed(title="Success!", description=f"Gave {xp} XP to {user.mention}", color=discord.Color.green())
    await ctx.respond(embed=embed)

@bot.slash_command(name='setup_ignorechannel', description='Ignore a channel for any XP gain')
async def setup_ignorechannel(ctx):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined" or setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role or administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    if setup.is_ic(ctx.channel.id):
        embed = discord.Embed(title="Error!", description="This channel is already ignored for XP gain", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    setup.set_ic(ctx.guild.id, ctx.channel.id)
    embed = discord.Embed(title="Success!", description=f"Ignored channel {ctx.channel.mention} for XP gain", color=discord.Color.green())
    await ctx.respond(embed=embed)

@bot.slash_command(name='setup_unignorechannel', description='Unignore a channel for any XP gain')
async def setup_unignorechannel(ctx):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined" or setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role or administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    if not setup.is_ic(ctx.channel.id):
        embed = discord.Embed(title="Error!", description="This channel is not ignored for XP gain", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    setup.rem_ic(ctx.guild.id, ctx.channel.id)
    embed = discord.Embed(title="Success!", description=f"Unignored channel {ctx.channel.mention} for XP gain", color=discord.Color.green())
    await ctx.respond(embed=embed)


@bot.slash_command(name='help', description='Get help on how to use the bot')
async def help(ctx, aspect: Option(str, "The aspect of the bot you need help with", required=False, choices=["money", "leveling", "items", "gambling", "other"], default="money")):
    await ctx.defer()
    embed = discord.Embed(title=f"Help ({aspect})", description="Here's how you can use the bot!")
    # List commands for each aspect and what they do
    if aspect == "money":
        embed.add_field(name="`/balance`", value="View your (or someone else's) balance", inline=False)
        embed.add_field(name="`/daily`", value="Claim your daily reward", inline=False)
        embed.add_field(name="`/work`", value="Work to earn money", inline=False)
        embed.add_field(name="`/crime`", value="Commit a crime to earn money (or fail and lose money)", inline=False)
        embed.add_field(name="`/coinflip`", value="Flip a coin", inline=False)
        embed.add_field(name="`/dice`", value="Roll a dice", inline=False)
    elif aspect == "leveling":
        embed.description += "Leveling up is based on the amount of XP you have. You can gain XP by sending messages in channels that are not ignored for XP gain. You can also receive XP from daily rewards, working, and committing crimes. When you level up, you receive a reward based on your level and you can also receive a role if the server owner has set it up."
        embed.add_field(name="`/rank`", value="View your (or someone else's) rank", inline=False)
        embed.add_field(name="`/leaderboard`", value="View the leaderboard of the server", inline=False)
        embed.add_field(name="`/lvlrewards`", value="View all the level rewards set for the server", inline=False)
        embed.add_field(name="`/lvlrewardremove`", value="Remove a role that is given to a user when they reach a certain level", inline=False)
    elif aspect == "items":
        embed.description += "Items can be used for various purposes, such as gaining XP, money, or other items. You can view your inventory with `/inventory` and use items with `/use`."
        embed.add_field(name="`/inventory`", value="View your inventory", inline=False)
        embed.add_field(name="`/use`", value="Use an item from your inventory", inline=False)
        embed.add_field(name="`/shop`", value="View the shop", inline=False)
    elif aspect == "gambling":
        embed.description += "You can gamble your money with the `/coinflip` and `/dice` commands. You can also open a gift box with the `/giftbox` command."
        embed.add_field(name="`/coinflip`", value="Flip a coin", inline=False)
        embed.add_field(name="`/dice`", value="Roll a dice", inline=False)
        embed.add_field(name="`/giftbox`", value="Open a gift box", inline=False)
        embed.add_field(name="`/slots`", value="Play the slots (loss = you lose your money, partialfail = you get your money back, win = you win 10x your bet)", inline=False)
    elif aspect == "other":
        embed.description += "Other commands that don't fit into the other categories."
        embed.add_field(name="`/help`", value="Get help on how to use the bot", inline=False)
        embed.add_field(name="[View Balance]", value="View the balance of the specified user (right-click on a user)", inline=False)
        embed.add_field(name="[View Rank]", value="View the rank of the specified user (right-click on a user)", inline=False)
        embed.add_field(name="[View Inventory]", value="View the inventory of the specified user (right-click on a user)", inline=False)
    await ctx.respond(embed=embed)

@bot.slash_command(name="search", description="Search for an item in the shop")
async def search(ctx, item: str):
    # this function lists all items that contain the search term
    await ctx.defer()
    itemlist = shop.get_processed()
    items = []
    for i in itemlist.keys():
        if item.lower() in i.lower():
            items.append(i)
    if len(items) == 0:
        embed = discord.Embed(title="Error!", description="No items found", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    embed = discord.Embed(title="Search Results", description="Here are the items that contain the search term")
    for index, item in enumerate(items):
        if index < 25:
            embed.add_field(name=item, value=f"Price: {itemlist[item]['price']} {constructCurrName()}", inline=False)
        else:
            new_embed = discord.Embed(title="Search Results (Continued)", description="Here are the remaining items that contain the search term")
            new_embed.add_field(name=item, value=f"Price: {itemlist[item]['price']} {constructCurrName()}", inline=False)
            await ctx.respond(embed=new_embed)
    
    await ctx.respond(embed=embed)


# This setup command wipes all the data for a specific user ID in the current guild
@setupgroup.command(name="wipeuser", description="Wipe all data for a specific user ID in the current guild")
async def setup_wipeuser(ctx, user: discord.User):
    await ctx.defer()
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined" or setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role or administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["modrole"] not in [role.id for role in ctx.author.roles] and setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the moderator role or the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    user_ = User()
    user_.load(user.id)
    user_.wipe(ctx.guild.id)
    embed = discord.Embed(title="Success!", description=f"Wiped all data for user {user.mention}", color=discord.Color.green())
    await ctx.respond(embed=embed)

@setupgroup.command(name="setmodifier", description="Set the modifier for a user")
async def setup_setmodifier(ctx, user: discord.User, modifier: float):
    await ctx.defer()
    if modifier < 0:
        embed = discord.Embed(title="Error!", description="The modifier cannot be less than 0", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    author = User()
    author.load(ctx.author.id)
    if author.banned:
        embed = discord.Embed(title="Rejected your request.", description="You are banned from using the bot", color=discord.Color.red())
    setup = GuildSetup()
    setup.load(ctx.guild.id)
    if setup.settings["modrole"] == "undefined" or setup.settings["adminrole"] == "undefined":
        embed = discord.Embed(title="Error!", description="No moderator role or administrator role has been set for this server", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    
    if setup.settings["modrole"] not in [role.id for role in ctx.author.roles] and setup.settings["adminrole"] not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(title="Error!", description="You need to have the moderator role or the administrator role to use this command", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    user_ = User()
    user_.load(user.id)
    user_.set_mod(ctx.guild.id, modifier)
    embed = discord.Embed(title="Success!", description=f"Set the modifier for user {user.mention} to {modifier}", color=discord.Color.green())
    await ctx.respond(embed=embed)


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user = User()
    user.load(message.author.id)
    user.give_msgc(message.guild.id)
    user.save()
    setup = GuildSetup()
    setup.load(message.guild.id)
    if setup.is_ic(message.channel.id):
        return
    if LastMessage.is_passed(message.author.id, linker.msgtimeout, message.guild.id) and not user.banned:
        xprandom = random.randint(linker.xprange[0], linker.xprange[1])
        if linker.effortboost:
            # Based on the amount of characters in the message, determine the multiplier. Required characters: eb_req, max multiplier: eb_max
            if len(message.content) >= linker.eb_req:
                # also multiply the random xp by the multiplier
                mul = len(message.content) / linker.eb_req
                if mul > linker.eb_max:
                    mul = linker.eb_max
                
                xprandom = round(xprandom * mul * user.getmodifiers(message.guild.id)) # multiply by the user's modifier
        resp = user.give_xp(xprandom, message.guild.id)
        print(f"Gave {xprandom} xp to {message.author.name}")
        LastMessage.set_lastmsgtime(message.author.id, message.guild.id)
        if resp == "newlvl":
            embed = discord.Embed(title="Level Up!", description=f"{message.author.mention} has leveled up to level {user.get_lvl(message.guild.id)}!", color=discord.Color.green())
            # Formula: Level * random(reward range min to reward range max) * (user modifier / 2) = reward
            reward = round(user.get_lvl(message.guild.id) * random.randint(linker.rewardrange[0], linker.rewardrange[1]) * (user.get_mod(message.guild.id) / 2))
            reward *= user.getmodifiers(message.guild.id)
            user.edit_money(reward, message.guild.id)
            
            embed.add_field(name="Reward", value=f"Received {reward} {constructCurrName()}", inline=False)
            if rr.hasreward(user.get_lvl(message.guild.id), message.guild.id):
                role = rr.get(user.get_lvl(message.guild.id), message.guild.id)
                try:
                    await message.author.add_roles(discord.utils.get(message.guild.roles, id=role))
                    embed.add_field(name="Reward Role", value=f"As an additional reward, you have been given the role {discord.utils.get(message.guild.roles, id=role).mention}", inline=False)
                except:
                    embed.add_field(name="Reward Role", value=f"We wanted to give you the role {discord.utils.get(message.guild.roles, id=role).mention} as an additional reward, but an error occurred", inline=False)
            await message.channel.send(embed=embed)
    else:
        pass

@bot.event
async def on_member_join(member):
    if member.bot:
        return
    user = User()
    user.load(member.id)
    user.save()

bot.run(TOKEN)
