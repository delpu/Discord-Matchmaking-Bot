import os
import json
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import cogs.matchmaking

## Config
def config(filename: str = "config"):
    try:
        with open(f"{filename}.json", encoding='utf8') as data:
            return json.load(data)
    except FileNotFoundError:
        raise FileNotFoundError("Config not found!")

cfg = config()

## Bot Setup
intents = discord.Intents.all() 
bot = commands.Bot(command_prefix="!",
owner_ids=cfg["owners"],
case_insensitive=True,
help_command=None,
intents=intents
)

def printl(text):
    print(f"[#] " + text)

#load cogs
async def load_cogs() -> None:
    """
    The code in this function is executed whenever the bot will start.
    """
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                printl(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                printl(
                    f"Failed to load extension {extension}\n{exception}")

## Setting and starting Bot
my_server = "615663613822238731"
@bot.event
async def on_ready():
    servers = [] 
    for server in bot.guilds:
        servers.append(server.name)
        if server != my_server:
            await server.leave()

    print("Logged in as: " + bot.user.name)
    print("Bot ID: " + str(bot.user.id))
    print("Bot is online in: {} servers \n {}".format(len(servers), servers))
    activity = discord.Activity(type=discord.ActivityType.playing, name=cfg["activity"])
    bot.add_view(cogs.matchmaking.Queue2v2())
    bot.add_view(cogs.matchmaking.Queue3v3())
    await bot.tree.sync()
    await bot.change_presence(status=discord.Status(cfg["status"]), activity=activity)

@bot.event
async def on_server_join(server):
    if server != my_server:
        await server.leave()

asyncio.run(load_cogs())
bot.run(cfg["token"])