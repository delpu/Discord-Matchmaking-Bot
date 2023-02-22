import discord
from discord.ext import commands
from discord.ext.commands import errors

class Error_Handler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        if isinstance(err, errors.MissingRequiredArgument) or isinstance(err, errors.BadArgument):
            embed = discord.Embed(title="📚 Wrong Arguments", description="Please use help if u have any problems.", color=0xff6961)
            await ctx.send(embed=embed, delete_after=5.0)
            await ctx.message.delete()
        elif isinstance(err, errors.CheckFailure):
            pass
        elif isinstance(err, errors.MaxConcurrencyReached):
            embed = discord.Embed(title=":stopwatch: Cooldown", description="Hey! Slow down a little, finish previous commands progress first!", color=0x98baff)
            await ctx.send(embed=embed, delete_after=5.0)
            await ctx.message.delete()
        elif isinstance(err, errors.CommandOnCooldown):
            embed = discord.Embed(title=":stopwatch: Cooldown", description="Hey! Slow down a little, this command is on cooldown. Try again in {:.0f}s".format(err.retry_after), color=0x98baff)
            await ctx.send(embed=embed, delete_after=5.0)
            await ctx.message.delete()
        elif isinstance(err, errors.CommandNotFound):
            pass
        elif isinstance(err, errors.MissingPermissions):
            embed = discord.Embed(title="🔑 Missing Permissions", description="You don't have permission to use that command.", color=0xff6961)
            await ctx.send(embed=embed, delete_after=5.0)
            await ctx.message.delete()
        elif isinstance(err, errors.BotMissingPermissions):
            pass
        elif isinstance(err, errors.BotMissingRole):
            pass
        elif isinstance(err, errors.BotMissingAnyRole):
            pass

async def setup(bot):
    await bot.add_cog(Error_Handler(bot)) 