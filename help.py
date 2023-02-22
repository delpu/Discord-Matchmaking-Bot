import discord
from discord.ext import commands

class Help_cmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            embed=discord.Embed(title="📖 Help", color=0x75d968)
            embed.add_field(name="User Commands", value="!stats <@name> - shows player stats \n !leaderboards solo/team \n !lost or !lose - signifies a match loser \n !need_sub - looking for a replacement player \n !notifications on/off - turns on or off dm notifications", inline=True)
            embed.add_field(name="Admin Commands", value="!cards - post bot queue cards \n !set_cards - sets matchmaking info channel \n !set_log - sets logs channel \n !cancel_match - cancels match \n !choose_winner team1/team2 - picks winner of match \n !reload - realoads bot db \n !verify @mention region nickname", inline=False)
            await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title="📖 Help", color=0x75d968)
            embed.add_field(name="User Commands", value="!stats <@name> - shows player stats \n !leaderboards solo/team \n !lost or !lose - signifies a match loser \n !need_sub - looking for a replacement player \n !notifications on/off - turns on or off dm notifications", inline=True)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help_cmd(bot)) 