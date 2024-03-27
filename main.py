from dotenv import load_dotenv
import os
from management.shop import Shop
from management.modlist import GuildSetup
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
    embed = discord.Embed(title=f"{user.name}'s balance", description=f"Balance: {user_.get_balance(ctx.guild.id)} {emoji if linker.needicon else ''} {linker.currname}", color=discord.Color.random())
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
        self.inventory = user.inventory[guildid]

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
    lrv = ShopLRView(ctx, embed, itemlist, ctx.guild.id)
    await lrv.pre_rendder()
    await ctx.respond(embed=embed, view=lrv)

setupgroup = bot.create_group(name="setup", description="Setup the bot for your server")

@setupgroup.command(name="modrole", description="Set the moderator role for the server")
@commands.has_permissions(administrator=True)
async def modrole(ctx, role: discord.Role):
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
    if linker.needicon:
        hostguild = bot.get_guild(linker.hostguildid)
        mojis = hostguild.emojis
        for moji in mojis:
            if moji.id == linker.emojiid:
                emoji = str(moji)
    embed = discord.Embed(title="Success!", description=f"Gave {amount} {emoji if linker.needicon else ''} {linker.currname} to {user.mention}", color=discord.Color.green())
    await ctx.respond(embed=embed)


bot.run(TOKEN)