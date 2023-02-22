import discord
import random
import sqlite3
import os, sys
import asyncio
import math
from async_timeout import timeout
from discord.ext import commands
from discord import app_commands

aqua = 0x3BADFF

# Function to calculate the Probability

def Probability(rating1, rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

# Elo Calc
    
def EloRating(Ra, Rb):
    K = 11
    old_winnerELO = Ra
    #old_loserELO = Rb

    Pb = Probability(Ra, Rb)
  
    Pa = Probability(Rb, Ra)
  
    Ra = Ra + K * (1 - Pa)
    Rb = Rb + K * (0 - Pb)

    return (math.ceil(abs(old_winnerELO - Ra)))

#avg function
def Average(lst):
    return sum(lst) / len(lst)

#Buttons View

class Queue2v2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label='Join 2v2 Queue', style=discord.ButtonStyle.green, custom_id='join_queue:2v2')
    async def join2v2queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        list2v2 = matchcog.queue_players["2v2"]
        list3v3 = matchcog.queue_players["3v3"]
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        cardMessage = interaction.message
        message2v2 = matchcog.queue_messages["2v2"]
        channel = interaction.channel

        #await interaction.response.defer()
        #try:
        #    matchcog.insert("INSERT INTO player(discord_id, name) VALUES({}, '{}')".format(member.id, member.name))
        #except:
        #    pass

        if member in list2v2 or member in list3v3:
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f'You are already in queue!', ephemeral=True)
        elif inMatch in member.roles:
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send("You cannot join a ranked queue while in a match!", ephemeral=True)
        else:
            if str(cardMessage.id) == message2v2:
                #await interaction.response.defer()
                list2v2.append(member)
                embed = discord.Embed(title="Ranked Queue 2v2", description="To join or leave queue use buttons below.", colour=aqua)
                embed.add_field(name='Players',value=matchcog.queue_string(list2v2),inline=True)
                embed.add_field(value='** **', name="{}/{}".format(len(list2v2), 4),inline=True)
                await interaction.response.edit_message(embeds=[embed])
                if len(list2v2) == 4:
                    #Get 4 players
                    players = []
                    for x in range(4):
                        players.append(list2v2.pop(0))

                    for player in players:
                        await player.add_roles(inMatch)
                    
                    #Reset Embed
                    embed = discord.Embed(title="Ranked Queue 2v2", description="To join or leave queue use buttons below.", colour=aqua)
                    embed.add_field(name='Players',value=matchcog.queue_string(list2v2),inline=True)
                    embed.add_field(value='** **', name="{}/{}".format(len(list2v2), 4),inline=True)
                    await cardMessage.edit(embeds=[embed])

                    #Get Match ID
                    match_id = matchcog.retrive("SELECT value FROM config WHERE variable='MATCH_ID'")[0]
                    match_fixed = str((int(match_id)+1))
                    matchcog.insert("UPDATE config SET value = '{}' WHERE variable='MATCH_ID'".format(match_fixed))
                    #vc_name = self.fix_match(match_fixed, 0)
                    match_id = matchcog.fix_match(match_fixed)
                    
                    #Get the match category
                    match_category = matchcog.retrive("SELECT value FROM config WHERE variable='MATCH_CATEGORY'")[0]

                    #Create the category
                    match_category = discord.utils.get(channel.guild.categories, id=int(match_category))
                    if not match_category:
                        match_category = await channel.guild.create_category(name="Matches")
                        matchcog.insert("UPDATE config SET value='{}' WHERE variable='MATCH_CATEGORY'".format(match_category.id))

                    text_channel  = await match_category.create_text_channel(name=match_id)
                    #voice_channel1 = await match_category.create_voice_channel(name=vc_name+"Team 1")
                    #voice_channel2 = await match_category.create_voice_channel(name=vc_name+"Team 2")
                    for player in players:
                        await text_channel.set_permissions(player, view_channel=True)
                        await text_channel.set_permissions(player, send_messages=True)
                        #await voice_channel1.set_permissions(player, view_channel=True)
                        #await voice_channel2.set_permissions(player, view_channel=True)

                    await text_channel.set_permissions(channel.guild.default_role, view_channel=True)
                    await text_channel.set_permissions(channel.guild.default_role, send_messages=False)

                    teams = matchcog.create_team(players)

                    #Add the match to the
                    matchcog.matches[text_channel.id] = {
                    "text_channel": text_channel,
                    #"voice_channel": [voice_channel1, voice_channel2],
                    "team1": teams['team1'],
                    "team2": teams['team2'],
                    "match_id": match_fixed
                    }

                    #Notifications
                    #for player in players:
                    #    dm_status = matchcog.retrive("SELECT notifications FROM player WHERE discord_id={}".format(player.id))
                    #    if dm_status == (1,):
                    #        embed = discord.Embed(title="", description="Your match {0.mention} is ready!".format(text_channel), colour = 0x77dd77)
                    #        await player.send(embed=embed)

                    
                    if matchcog.log_channel:
                        embed = discord.Embed(title="", description="{0.mention} has been generated".format(text_channel), colour = 0x77dd77)
                        await matchcog.log_channel.send(embed=embed)

                    text = " "
                    for player in players:
                        text += player.mention
                    await text_channel.send(text, delete_after=1)

                    #Send Admin Panel
                    embed = discord.Embed(title =":tools: Admin Panel", colour = 0xE7625F)
                    embed.add_field(name='', value='Admin Tools to use in emergency cases!', inline=False)
                    await text_channel.send(embed=embed, view=AdminPanel())

                    #Teams
                    embed = discord.Embed(title ="{}".format(match_id), colour = aqua)
                    embed.add_field(name='Team 1', value=matchcog.queue_string(teams['team1']), inline=True)
                    embed.add_field(name='Team 2', value=matchcog.queue_string(teams['team2']), inline=True)
                    embed.add_field(name='Recommended Spar Location', value="🐸 Land Of Toads", inline=False)
                    await text_channel.send(embed=embed)

                    #Send UserPanel
                    embed = discord.Embed(title =":warning: Important Instructions", colour = 0x77dd77)
                    embed.add_field(name='How to properly end the duel?', value='Winning or losing team should provide a screenshot of match result. \n After that one of teams should use a proper button below. \n If one of players is afk or is not able to take a part in spar players can vote to cancel a match.', inline=False)
                    await text_channel.send(embed=embed, view=UserPanel())

                    try:
                        matchcog.insert("INSERT INTO player(discord_id, name) VALUES({}, '{}')".format(member.id, member.name))
                    except:
                        pass
                else:
                    await asyncio.sleep(matchcog.queue_kick_time)
                    if member in list2v2:
                        list2v2.remove(member)
                        if list2v2 == []:
                            embed = discord.Embed(title ="Ranked Queue 2v2", description="To join or leave queue use buttons below..", colour=aqua)
                            embed.add_field(name='Players',value='** **',inline=True)
                            embed.add_field(value='** **', name="{}/{}".format(len(list2v2), 4),inline=True)
                        else:
                            embed = discord.Embed(title ="Ranked Queue 2v2", description="To join or leave queue use buttons below.", colour=aqua)
                            embed.add_field(name='Players',value=matchcog.queue_string(list2v2),inline=True)
                            embed.add_field(value='** **', name="{}/{}".format(len(list2v2), 4),inline=True)
                            await cardMessage.edit(embeds=[embed])
                        if matchcog.log_channel:
                            embed = discord.Embed(title="{}".format(member), description="was kicked from 2v2 queue to prevent afk!", colour = aqua)
                            await matchcog.log_channel.send(embed=embed)
                            embed = discord.Embed(title ="Ranked Queue 2v2", description="To join or leave queue use buttons below.", colour=aqua)
                            embed.add_field(name='Players',value=matchcog.queue_string(list2v2),inline=True)
                            embed.add_field(value='** **', name="{}/{}".format(len(list2v2), 4),inline=True)
                            await cardMessage.edit(embeds=[embed])


    @discord.ui.button(label='Leave Queue', style=discord.ButtonStyle.red, custom_id='leave_queue:2v2')
    async def leavequeue2v2(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        list2v2 = matchcog.queue_players["2v2"]
        member = interaction.user
        cardMessage = interaction.message
        message2v2 = matchcog.queue_messages["2v2"]
        if str(cardMessage.id) == message2v2:
            if member not in list2v2:
                await interaction.response.send_message("You are not in a 2v2 queue!", ephemeral=True)
            else:
                try:
                    list2v2.remove(member)
                except:
                    pass
                if list2v2 == []:
                    embed = discord.Embed(title="Ranked Queue 2v2", description="To join or leave queue use buttons below.", colour=aqua)
                    embed.add_field(name='Players',value="** **",inline=True)
                    embed.add_field(value='** **', name="{}/{}".format(len(list2v2), 4),inline=True)
                    await interaction.response.send_message("You left a 2v2 queue!", ephemeral=True)
                else:
                    embed = discord.Embed(title="Ranked Queue 2v2", description="To join or leave queue use buttons below.", colour=aqua)
                    embed.add_field(name='Players',value=matchcog.queue_string(list2v2),inline=True)
                    embed.add_field(value='** **', name="{}/{}".format(len(list2v2), 4),inline=True)
                    await interaction.response.send_message("You left a 2v2 queue!", ephemeral=True)
                await cardMessage.edit(embeds=[embed])
        else:
            await interaction.response.send_message("Something went wrong...", ephemeral=True)



class Queue3v3(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label='Join 3v3 Queue', style=discord.ButtonStyle.green, custom_id='join_queue:3v3')
    async def join3v3queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        list2v2 = matchcog.queue_players["2v2"]
        list3v3 = matchcog.queue_players["3v3"]
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        cardMessage = interaction.message
        message3v3 = matchcog.queue_messages["3v3"]
        channel = interaction.channel

        #await interaction.response.defer()
        #try:
        #    matchcog.insert("INSERT INTO player(discord_id, name) VALUES({}, '{}')".format(member.id, member.name))
        #except:
        #    pass

        if member in list2v2 or member in list3v3:
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(f'You are already in queue!', ephemeral=True)
        elif inMatch in member.roles:
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send("You cannot join a ranked queue while in a match!", ephemeral=True)
        else:
            if str(cardMessage.id) == message3v3:
                #await interaction.response.defer()
                list3v3.append(member)
                embed = discord.Embed(title="Ranked Queue 3v3", description="To join or leave queue use buttons below.", colour=aqua)
                embed.add_field(name='Players',value=matchcog.queue_string(list3v3),inline=True)
                embed.add_field(value='** **', name="{}/{}".format(len(list3v3), 6),inline=True)
                await interaction.response.edit_message(embeds=[embed])
                if len(list3v3) == 6:
                    #Get 6 players
                    players = []
                    for x in range(6):
                        players.append(list3v3.pop(0))
                    
                    for player in players:
                        await player.add_roles(inMatch)

                    #Reset Embed
                    embed = discord.Embed(title="Ranked Queue 3v3", description="To join or leave queue use buttons below.", colour=aqua)
                    embed.add_field(name='Players',value=matchcog.queue_string(list3v3),inline=True)
                    embed.add_field(value='** **', name="{}/{}".format(len(list3v3), 6),inline=True)
                    await cardMessage.edit(embeds=[embed])

                    #Get Match ID
                    match_id = matchcog.retrive("SELECT value FROM config WHERE variable='MATCH_ID'")[0]
                    match_fixed = str((int(match_id)+1))
                    matchcog.insert("UPDATE config SET value = '{}' WHERE variable='MATCH_ID'".format(match_fixed))
                    #vc_name = self.fix_match(match_fixed, 0)
                    match_id = matchcog.fix_match(match_fixed)
                    
                    #Get the match category
                    match_category = matchcog.retrive("SELECT value FROM config WHERE variable='MATCH_CATEGORY'")[0]

                    #Create the category
                    match_category = discord.utils.get(channel.guild.categories, id=int(match_category))
                    if not match_category:
                        match_category = await channel.guild.create_category(name="Matches")
                        matchcog.insert("UPDATE config SET value='{}' WHERE variable='MATCH_CATEGORY'".format(match_category.id))

                    text_channel  = await match_category.create_text_channel(name=match_id)
                    #voice_channel1 = await match_category.create_voice_channel(name=vc_name+"Team 1")
                    #voice_channel2 = await match_category.create_voice_channel(name=vc_name+"Team 2")
                    for player in players:
                        await text_channel.set_permissions(player, view_channel=True)
                        await text_channel.set_permissions(player, send_messages=True)
                        #await voice_channel1.set_permissions(player, view_channel=True)
                        #await voice_channel2.set_permissions(player, view_channel=True)

                    await text_channel.set_permissions(channel.guild.default_role, view_channel=True)
                    await text_channel.set_permissions(channel.guild.default_role, send_messages=False)

                    teams = matchcog.create_team(players)

                    #Add the match to the
                    matchcog.matches[text_channel.id] = {
                    "text_channel": text_channel,
                    #"voice_channel": [voice_channel1, voice_channel2],
                    "team1": teams['team1'],
                    "team2": teams['team2'],
                    "match_id": match_fixed
                    }


                    #Notifications
                    #for player in players:
                    #    dm_status = matchcog.retrive("SELECT notifications FROM player WHERE discord_id={}".format(player.id))
                    #    if dm_status == (1,):
                    #        embed = discord.Embed(title="", description="Your match {0.mention} is ready!".format(text_channel), colour = 0x77dd77)
                    #        await player.send(embed=embed)

                    
                    if matchcog.log_channel:
                        embed = discord.Embed(title="", description="{0.mention} has been generated".format(text_channel), colour = 0x77dd77)
                        await matchcog.log_channel.send(embed=embed)

                    text = " "
                    for player in players:
                        text += player.mention
                    await text_channel.send(text, delete_after=1)

                    #Send Admin Panel
                    embed = discord.Embed(title =":tools: Admin Panel", colour = 0xE7625F)
                    embed.add_field(name='', value='Admin Tools to use in emergency cases!', inline=False)
                    await text_channel.send(embed=embed, view=AdminPanel())

                    #Teams
                    embed = discord.Embed(title ="{}".format(match_id), colour = aqua)
                    embed.add_field(name='Team 1', value=matchcog.queue_string(teams['team1']), inline=True)
                    embed.add_field(name='Team 2', value=matchcog.queue_string(teams['team2']), inline=True)
                    embed.add_field(name='Recommended Spar Location', value="🐸 Land Of Toads", inline=False)
                    await text_channel.send(embed=embed)

                    #Send UserPanel
                    embed = discord.Embed(title =":warning: Important Instructions", colour = 0x77dd77)
                    embed.add_field(name='How to properly end the duel?', value='Winning or losing team should provide a screenshot of match result. \n After that one of teams should use a proper button below. \n If one of players is afk or is not able to take a part in spar players can vote to cancel a match.', inline=False)
                    await text_channel.send(embed=embed, view=UserPanel())

                    try:
                        matchcog.insert("INSERT INTO player(discord_id, name) VALUES({}, '{}')".format(member.id, member.name))
                    except:
                        pass
                else:
                    await asyncio.sleep(matchcog.queue_kick_time)
                    if member in list3v3:
                        list3v3.remove(member)
                        if list3v3 == []:
                            embed = discord.Embed(title ="Ranked Queue 3v3", description="To join or leave queue use buttons below..", colour=aqua)
                            embed.add_field(name='Players',value='** **',inline=True)
                            embed.add_field(value='** **', name="{}/{}".format(len(list3v3), 6),inline=True)
                        else:
                            embed = discord.Embed(title ="Ranked Queue 3v3", description="To join or leave queue use buttons below.", colour=aqua)
                            embed.add_field(name='Players',value=matchcog.queue_string(list3v3),inline=True)
                            embed.add_field(value='** **', name="{}/{}".format(len(list3v3), 6),inline=True)
                            await cardMessage.edit(embeds=[embed])
                        if matchcog.log_channel:
                            embed = discord.Embed(title="{}".format(member), description="was kicked from 3v3 queue to prevent afk!", colour = aqua)
                            await matchcog.log_channel.send(embed=embed)
                            embed = discord.Embed(title ="Ranked Queue 3v3", description="To join or leave queue use buttons below.", colour=aqua)
                            embed.add_field(name='Players',value=matchcog.queue_string(list3v3),inline=True)
                            embed.add_field(value='** **', name="{}/{}".format(len(list3v3), 6),inline=True)
                            await cardMessage.edit(embeds=[embed])

    @discord.ui.button(label='Leave Queue', style=discord.ButtonStyle.red, custom_id='leave_queue:3v3')
    async def leavequeue3v3(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        list3v3 = matchcog.queue_players["3v3"]
        member = interaction.user
        cardMessage = interaction.message
        message3v3 = matchcog.queue_messages["3v3"]
        if str(cardMessage.id) == message3v3:
            if member not in list3v3:
                await interaction.response.send_message("You are not in a 3v3 queue!", ephemeral=True)
            else:
                try:
                    list3v3.remove(member)
                except:
                    pass
                if list3v3 == []:
                    embed = discord.Embed(title="Ranked Queue 3v3", description="To join or leave queue use buttons below.", colour=aqua)
                    embed.add_field(name='Players',value="** **",inline=True)
                    embed.add_field(value='** **', name="{}/{}".format(len(list3v3), 6),inline=True)
                    await interaction.response.send_message("You left a 3v3 queue!", ephemeral=True)
                else:
                    embed = discord.Embed(title="Ranked Queue 3v3", description="To join or leave queue use buttons below.", colour=aqua)
                    embed.add_field(name='Players',value=matchcog.queue_string(list3v3),inline=True)
                    embed.add_field(value='** **', name="{}/{}".format(len(list3v3), 6),inline=True)
                    await interaction.response.send_message("You left a 3v3 queue!", ephemeral=True)
                await cardMessage.edit(embeds=[embed])
        else:
            await interaction.response.send_message("Something went wrong...", ephemeral=True)

class AdminPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Team 1 WIN', style=discord.ButtonStyle.blurple, custom_id='admin_panel:team1')
    async def team1won(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        Staff = discord.utils.get(interaction.guild.roles, name="Staff")
        channel = interaction.channel
        if channel.id in matchcog.matches and Staff in member.roles:
            match = matchcog.matches.pop(channel.id)
            team1 = match['team1']
            team2 = match['team2']
            text_channel = match['text_channel']
            match_types = ["1v1", "2v2", "3v3"]
            match_type = match_types[len(team1)-1]
            match_id = match["match_id"]
            if match_type == "2v2":
                for player in team1:
                    player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team1_elo.append(player_elo[0])
                for player in team2:
                    player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team2_elo.append(player_elo1[0])
                #adding ELO
                team1_avg = round(Average(matchcog.team1_elo))
                team2_avg = round(Average(matchcog.team2_elo))
                elo_output = EloRating(team1_avg, team2_avg)
                for player  in team1:
                    matchcog.insert("UPDATE player SET wins_2v2 = wins_2v2 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                for player  in team2:
                    matchcog.insert("UPDATE player SET losses_2v2 = losses_2v2 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                matchcog.team1_elo.pop()
                matchcog.team2_elo.pop()
            else:
                #getting list done
                for player in team1:
                    player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team1_elo.append(player_elo[0])
                for player in team2:
                    player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team2_elo.append(player_elo1[0])
                #adding ELO
                team1_avg = round(Average(matchcog.team1_elo))
                team2_avg = round(Average(matchcog.team2_elo))
                elo_output = EloRating(team1_avg, team2_avg)
                for player  in team1:
                    matchcog.insert("UPDATE player SET wins_3v3 = wins_3v3 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                for player  in team2:
                    matchcog.insert("UPDATE player SET losses_3v3 = losses_3v3 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                matchcog.team1_elo.pop()
                matchcog.team2_elo.pop()
            embed_results=discord.Embed(title =f"Match Results (forced by {member})", color = 0xFFB62F)
            for player in team1:
                embed_results.add_field(name="Winning Team", value="{} | +{} ELO Points".format(player.mention, elo_output), inline=False)
            for player in team2:
                embed_results.add_field(name="Lost Team", value="\n{} | -{} ELO Points".format(player.mention, elo_output), inline=False)
            if matchcog.log_channel:
                embed = discord.Embed(title="Match #{} Log".format(match_id), description=matchcog.get_log_text(team1, team2,1), colour = aqua)
                await matchcog.log_channel.send(embed=embed)
            await text_channel.send(embed=embed_results)
        else:
            await interaction.response.send_message("The channel is not a match channel or you don't have permissions.", ephemeral=True)
        await interaction.response.send_message("Score has been registered. This channel will be deleted after 1 minute", ephemeral=False)
        await asyncio.sleep(60)
        try:
            await match['text_channel'].delete()
            await match['voice_channel'][0].delete()
            await match['voice_channel'][1].delete()
        except:
            pass

    @discord.ui.button(label='Team 2 WIN', style=discord.ButtonStyle.blurple, custom_id='admin_panel:team2')
    async def team2won(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        Staff = discord.utils.get(interaction.guild.roles, name="Staff")
        channel = interaction.channel
        if channel.id in matchcog.matches and Staff in member.roles:
            match = matchcog.matches.pop(channel.id)
            team1 = match['team1']
            team2 = match['team2']
            text_channel = match['text_channel']
            match_types = ["1v1", "2v2", "3v3"]
            match_type = match_types[len(team1)-1]
            match_id = match["match_id"]
            if match_type == "2v2":
                for player in team1:
                    player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team1_elo.append(player_elo[0])
                for player in team2:
                    player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team2_elo.append(player_elo1[0])
                #adding ELO
                team1_avg = round(Average(matchcog.team1_elo))
                team2_avg = round(Average(matchcog.team2_elo))
                elo_output = EloRating(team1_avg, team2_avg)
                for player  in team2:
                    matchcog.insert("UPDATE player SET wins_2v2 = wins_2v2 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                for player  in team1:
                    matchcog.insert("UPDATE player SET losses_2v2 = losses_2v2 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                matchcog.team1_elo.pop()
                matchcog.team2_elo.pop()
            else:
                #getting list done
                for player in team1:
                    player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team1_elo.append(player_elo[0])
                for player in team2:
                    player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                    matchcog.team2_elo.append(player_elo1[0])
                #adding ELO
                team1_avg = round(Average(matchcog.team1_elo))
                team2_avg = round(Average(matchcog.team2_elo))
                elo_output = EloRating(team2_avg, team1_avg)
                for player  in team2:
                    matchcog.insert("UPDATE player SET wins_3v3 = wins_3v3 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                for player  in team1:
                    matchcog.insert("UPDATE player SET losses_3v3 = losses_3v3 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                    await player.remove_roles(inMatch)
                matchcog.team1_elo.pop()
                matchcog.team2_elo.pop()
            embed_results=discord.Embed(title =f"Match Results (forced by {member})", color = 0xFFB62F)
            for player in team2:
                embed_results.add_field(name="Winning Team", value="{} | +{} ELO Points".format(player.mention, elo_output), inline=False)
            for player in team1:
                embed_results.add_field(name="Lost Team", value="\n{} | -{} ELO Points".format(player.mention, elo_output), inline=False)
            if matchcog.log_channel:
                embed = discord.Embed(title="Match #{} Log".format(match_id), description=matchcog.get_log_text(team2, team1,1), colour = aqua)
                await matchcog.log_channel.send(embed=embed)
            await text_channel.send(embed=embed_results)
        else:
            await interaction.response.send_message("The channel is not a match channel or you don't have permissions.", ephemeral=True)

        await interaction.response.send_message("Score has been registered. This channel will be deleted after 1 minute", ephemeral=False)
        await asyncio.sleep(60)
        try:
            await match['text_channel'].delete()
            await match['voice_channel'][0].delete()
            await match['voice_channel'][1].delete()
        except:
            pass

    @discord.ui.button(label='Cancel Match', style=discord.ButtonStyle.red, custom_id='admin_panel:cancel')
    async def admincancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        Staff = discord.utils.get(interaction.guild.roles, name="Staff")
        channel = interaction.channel
        if channel.id in matchcog.matches and Staff in member.roles:
            match = matchcog.matches.pop(channel.id)
            team1 = match['team1']
            team2 = match['team2']
            text_channel = match['text_channel']
            match_types = ["1v1", "2v2", "3v3"]
            match_type = match_types[len(team1)-1]
            match_id = match["match_id"]
            for player in team1:
                await player.remove_roles(inMatch)
            for player  in team2:
                await player.remove_roles(inMatch)
            await interaction.response.send_message("The match has been cancelled. This channel will be deleted after 1 mintue", ephemeral=False)
            if matchcog.log_channel:
                embed = discord.Embed(title ="Match #{} Log".format(match_id), description="This match has been cancelled", colour = aqua)
                await matchcog.log_channel.send(embed=embed)
            await asyncio.sleep(60)
            try:
                await match['text_channel'].delete()
                await match['voice_channel'][0].delete()
                await match['voice_channel'][1].delete()
            except:
                pass
        else:
            await interaction.response.send_message("The channel is not a match channel or you don't have permissions.", ephemeral=True)

class UserPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Won (disabled)', style=discord.ButtonStyle.green, custom_id='user_panel:won', disabled=True)
    async def userwon(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        channel = interaction.channel
        
        if channel.id in matchcog.matches:
            match = matchcog.matches.pop(channel.id)
            team1 = match['team1']
            team2 = match['team2']
            text_channel = match['text_channel']
            match_types = ["1v1", "2v2", "3v3"]
            match_type = match_types[len(team1)-1]
            match_id = match["match_id"]
            if member not in team1 and member not in team2:
                await interaction.response.send_message("You are not a part of this match!", ephemeral=True)
                return
            if member in team1:
                if match_type == "2v2":
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    team1_avg = round(Average(matchcog.team1_elo))
                    team2_avg = round(Average(matchcog.team2_elo))
                    elo_output = EloRating(team1_avg, team2_avg)
                    for player  in team1:
                        matchcog.insert("UPDATE player SET wins_2v2 = wins_2v2 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET losses_2v2 = losses_2v2 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()
                else:
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    team1_avg = round(Average(matchcog.team1_elo))
                    team2_avg = round(Average(matchcog.team2_elo))
                    elo_output = EloRating(team1_avg, team2_avg)
                    for player  in team1:
                        matchcog.insert("UPDATE player SET wins_3v3 = wins_3v3 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET losses_3v3 = losses_3v3 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()
            else:
                if match_type == "2v2":
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    team1_avg = round(Average(matchcog.team1_elo))
                    team2_avg = round(Average(matchcog.team2_elo))
                    elo_output = EloRating(team2_avg, team1_avg)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET wins_2v2 = wins_2v2 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team1:
                        matchcog.insert("UPDATE player SET losses_2v2 = losses_2v2 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()
                else:
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    team1_avg = round(Average(matchcog.team1_elo))
                    team2_avg = round(Average(matchcog.team2_elo))
                    elo_output = EloRating(team2_avg, team1_avg)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET wins_3v3 = wins_3v3 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team1:
                        matchcog.insert("UPDATE player SET losses_3v3 = losses_3v3 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()

            embed_results=discord.Embed(title ="Match Results", color = 0xFFB62F)
            if member in team2:
                for player in team2:
                    embed_results.add_field(name="Winning Team", value="{} | +{} ELO Points".format(player.mention, elo_output), inline=False)
                for player in team1:
                    embed_results.add_field(name="Lost Team", value="\n{} | -{} ELO Points".format(player.mention, elo_output), inline=False)
                if matchcog.log_channel:
                    embed = discord.Embed(title="Match #{} Log".format(match_id), description=matchcog.get_log_text(team1, team2, 2), colour = aqua)
                    await matchcog.log_channel.send(embed=embed)
            else:
                for player in team1:
                    embed_results.add_field(name="Winning Team", value="{} | +{} ELO Points".format(player.mention, elo_output), inline=False)
                for player in team2:
                    embed_results.add_field(name="Lost Team", value="\n{} | -{} ELO Points".format(player.mention, elo_output), inline=False)
                if matchcog.log_channel:
                    embed = discord.Embed(title="Match #{} Log".format(match_id), description=matchcog.get_log_text(team1, team2,1), colour = aqua)
                    await matchcog.log_channel.send(embed=embed)

            await text_channel.send(embed=embed_results)
            await interaction.response.send_message("Score has been registered. This channel will be deleted after 1 minute!", ephemeral=False)
            await asyncio.sleep(60)
            try:
                await text_channel.delete()
                await match['voice_channel'][0].delete()
                await match['voice_channel'][1].delete()
            except:
                pass
        else:
            await interaction.response.send_message("This is not a match channel!", ephemeral=True)

    @discord.ui.button(label='Lost', style=discord.ButtonStyle.red, custom_id='user_panel:lost')
    async def userlost(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        channel = interaction.channel
        
        if channel.id in matchcog.matches:
            match = matchcog.matches.pop(channel.id)
            team1 = match['team1']
            team2 = match['team2']
            text_channel = match['text_channel']
            match_types = ["1v1", "2v2", "3v3"]
            match_type = match_types[len(team1)-1]
            match_id = match["match_id"]
            if member not in team1 and member not in team2:
                await interaction.response.send_message("You are not a part of this match!", ephemeral=True)
                return
            if member in team2:
                if match_type == "2v2":
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    try:
                        team1_avg = round(Average(matchcog.team1_elo))
                        team2_avg = round(Average(matchcog.team2_elo))
                        elo_output = EloRating(team1_avg, team2_avg)
                    except:
                        pass
                    for player  in team1:
                        matchcog.insert("UPDATE player SET wins_2v2 = wins_2v2 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET losses_2v2 = losses_2v2 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()
                else:
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    try:
                        team1_avg = round(Average(matchcog.team1_elo))
                        team2_avg = round(Average(matchcog.team2_elo))
                        elo_output = EloRating(team1_avg, team2_avg)
                    except:
                        pass
                    for player  in team1:
                        matchcog.insert("UPDATE player SET wins_3v3 = wins_3v3 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET losses_3v3 = losses_3v3 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()
            else:
                if match_type == "2v2":
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    team1_avg = round(Average(matchcog.team1_elo))
                    team2_avg = round(Average(matchcog.team2_elo))
                    elo_output = EloRating(team2_avg, team1_avg)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET wins_2v2 = wins_2v2 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team1:
                        matchcog.insert("UPDATE player SET losses_2v2 = losses_2v2 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()
                else:
                    #getting list done
                    for player in team1:
                        player_elo = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team1_elo.append(player_elo[0])
                    for player in team2:
                        player_elo1 = matchcog.retrive("SELECT team_elo FROM player WHERE discord_id={}".format(player.id))
                        matchcog.team2_elo.append(player_elo1[0])
                    #adding ELO
                    team1_avg = round(Average(matchcog.team1_elo))
                    team2_avg = round(Average(matchcog.team2_elo))
                    elo_output = EloRating(team2_avg, team1_avg)
                    for player  in team2:
                        matchcog.insert("UPDATE player SET wins_3v3 = wins_3v3 + 1, matches = matches + 1, team_elo = team_elo + {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    for player  in team1:
                        matchcog.insert("UPDATE player SET losses_3v3 = losses_3v3 + 1, matches = matches + 1, team_elo = team_elo - {} WHERE discord_id={}".format(elo_output,player.id))
                        await player.remove_roles(inMatch)
                    matchcog.team1_elo.pop()
                    matchcog.team2_elo.pop()

            embed_results=discord.Embed(title ="Match Results", color = 0xFFB62F)
            if member in team1:
                for player in team2:
                    embed_results.add_field(name="Winning Team", value="{} | +{} ELO Points".format(player.mention, elo_output), inline=False)
                for player in team1:
                    embed_results.add_field(name="Lost Team", value="\n{} | -{} ELO Points".format(player.mention, elo_output), inline=False)
                if matchcog.log_channel:
                    embed = discord.Embed(title="Match #{} Log".format(match_id), description=matchcog.get_log_text(team1, team2, 2), colour = aqua)
                    await matchcog.log_channel.send(embed=embed)
            else:
                for player in team1:
                    embed_results.add_field(name="Winning Team", value="{} | +{} ELO Points".format(player.mention, elo_output), inline=False)
                for player in team2:
                    embed_results.add_field(name="Lost Team", value="\n{} | -{} ELO Points".format(player.mention, elo_output), inline=False)
                if matchcog.log_channel:
                    embed = discord.Embed(title="Match #{} Log".format(match_id), description=matchcog.get_log_text(team1, team2,1), colour = aqua)
                    await matchcog.log_channel.send(embed=embed)

            await text_channel.send(embed=embed_results)
            await interaction.response.send_message("Score has been registered. This channel will be deleted after 1 minute!", ephemeral=False)
            await asyncio.sleep(60)
            try:
                await text_channel.delete()
                await match['voice_channel'][0].delete()
                await match['voice_channel'][1].delete()
            except:
                pass
        else:
            await interaction.response.send_message("This is not a match channel!", ephemeral=True)

    @discord.ui.button(label='Cancel Match (Vote)', style=discord.ButtonStyle.danger, custom_id='user_panel:cancel')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        matchcog = interaction.client.get_cog("matchmaking")
        member = interaction.user
        inMatch = discord.utils.get(interaction.guild.roles, name="In Match") #change to discord.utils.get(interaction.guild.roles, id="database")
        channel = interaction.channel
        
        if channel.id in matchcog.matches:
            match = matchcog.matches[channel.id]
            team1 = match['team1']
            team2 = match['team2']
            team_count = (len(team1)+len(team2)) /2
            match_id = match["match_id"]
            if member not in team1 and member not in team2:
                await interaction.response.send_message("You are not a part of this match!", ephemeral=True)
                return
            if f'{channel.id}' not in matchcog.cancel_votes:
                matchcog.cancel_votes[f'{channel.id}'] = 1
            else:
                matchcog.cancel_votes[f'{channel.id}'] = matchcog.cancel_votes[f'{channel.id}'] + 1
            
            if matchcog.cancel_votes[f'{channel.id}'] == (team_count+1):
                matchcog.matches.pop(channel.id)
                for player  in team1:
                    await player.remove_roles(inMatch)
                for player  in team2:
                    await player.remove_roles(inMatch)
                await interaction.response.send_message("The match has been cancelled. This channel will be deleted after 1 mintue", ephemeral=False)
                if matchcog.log_channel:
                    embed = discord.Embed(title ="Match #{} Log".format(match_id), description="This match has been cancelled", colour = aqua)
                    await matchcog.log_channel.send(embed=embed)
                await asyncio.sleep(60)
                try:
                    await match['text_channel'].delete()
                    await match['voice_channel'][0].delete()
                    await match['voice_channel'][1].delete()
                except:
                    pass
            else:
                current_votes = matchcog.cancel_votes[f'{channel.id}']
                await interaction.response.send_message(f"**{current_votes}/{round(team_count+1)}** votes to cancel a match. Press CANCEL MATCH button to vote.", ephemeral=False)
        else:
            await interaction.response.send_message("This is not a match channel!", ephemeral=True)




class matchmaking(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.queue_players = {
            "1v1":[],
            "2v2":[],
            "3v3":[]
        }
        
        self.queue_messages = {}
        self.matches = {}
        self.log_channel = 0
        self.cards_channel = 0
        self.queue_kick_time = 600
        self.team1_elo = []
        self.team2_elo = []
        self.cancel_votes = {}


    #Connection to database
    def connect(self):
        connection = sqlite3.connect(os.path.join(sys.path[0],"matchmaking.db"))
        return connection

    #SQL queries
    #insertinto DB
    def insert(self, query):
        connection  = self.connect()
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        connection.close()

    #retrive from DB
    def retrive(self, query, check=1):
        connection  = self.connect()
        cursor = connection.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        return data[0] if check else data


    #fix match number
    def fix_match(self, number, check=1):
        count = len(str(number))
        string = str(number)
        string = "0"*(4-len(str(number))) + number
        if check:
            return "🏆 Match #{}".format(string)
        else:
            return "M #{} ".format(string)

    #create_team
    def create_team(self, players):
        random.shuffle(players)
        return {"team1":players[:-(len(players)//2)], "team2":players[(len(players)//2):]}

    #convert queue to string
    def queue_string(self, queue):
        text = ""
        for member in queue:
            text = text + "\n" + member.mention
        return text if text else " "


    #buttons
    @commands.has_permissions(administrator=True)
    @commands.command()
    async def prepare(self, ctx):
        #2v2
        embed = discord.Embed(title ="Ranked Queue 2v2", description="To join or leave queue use buttons below.", colour = aqua)
        embed.add_field(name='Players',value=self.queue_string(self.queue_players["2v2"]),inline=True)
        embed.add_field(name='0/4', value="** **",inline=True)
        message = await ctx.send(embed=embed, view=Queue2v2())
        self.queue_messages['2v2'] = message.id
        self.insert("UPDATE config SET value='{}' WHERE variable='2V2_MESSAGE'".format(message.id))
        #3v3
        embed = discord.Embed(title ="Ranked Queue 3v3", description="To join or leave queue use buttons below.", colour = aqua)
        embed.add_field(name='Players',value=self.queue_string(self.queue_players["3v3"]),inline=True)
        embed.add_field(name='0/6', value="** **",inline=True)
        message = await ctx.send(embed=embed, view=Queue3v3())
        self.queue_messages['3v3'] = message.id
        self.insert("UPDATE config SET value='{}' WHERE variable='3V3_MESSAGE'".format(message.id))

    #on_ready: load everything
    @commands.Cog.listener()
    async def on_ready(self):
        self.queue_messages['1v1'] = self.retrive("SELECT value FROM config WHERE variable='1V1_MESSAGE'")[0]
        self.queue_messages['2v2'] = self.retrive("SELECT value FROM config WHERE variable='2V2_MESSAGE'")[0]
        self.queue_messages['3v3'] = self.retrive("SELECT value FROM config WHERE variable='3V3_MESSAGE'")[0]
        self.log_channel = self.retrive("SELECT value FROM config WHERE variable='LOG_CHANNEL'")[0]
        self.log_channel = self.bot.get_channel(int(self.log_channel))
        self.cards_channel = self.retrive("SELECT value FROM config WHERE variable='CARD_CHANNEL'")[0]
        self.cards_channel = self.bot.get_channel(int(self.cards_channel))

    def get_log_text(self, team1, team2, winner):
        if winner == 1:
            text = "**Winners | Team1**\n"
            for player in team1:
                text = text + "{} ".format(player.mention)
            text = text + "\n" + "**Losers | Team2**\n"
            for player in team2:
                text = text + "{} ".format(player.mention)
            return text
        else:
            text = "**Winners | Team2**\n"
            for player in team2:
                text = text + "{} ".format(player.mention)
            text = text + "\n" + "**Losers | Team1**\n"
            for player in team1:
                text = text + "{} ".format(player.mention)
            return text

    @app_commands.command(name="leaderboard", description="Show ranked queues leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        data = self.retrive("SELECT discord_id, name, team_elo, wins_2v2+wins_3v3, wins_2v2+wins_3v3+losses_2v2+losses_3v3 FROM player ORDER BY team_elo DESC LIMIT 10", 0)
        embed = discord.Embed(title ="Ranked Queues Leaderboard", description="**TOP 10**", colour = aqua)
        for i, player in enumerate(data):
            embed.add_field(name="**#{}** {}".format(i+1, player[1]), value="Rating: ``{}`` Wins: ``{}`` Matches: ``{}``".format( player[2] ,player[3] ,player[4]) + "\n", inline=False)
        await interaction.response.defer()
        await interaction.followup.send(embed=embed)



    @app_commands.command(name="stats", description="Show ypur and other people statistics")
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        if member:
            member= member
        else:
            member = interaction.user
        try:
            self.insert("INSERT INTO player(discord_id, name) VALUES({}, '{}')".format(member.id, member.name))
        except:
            pass
        member_stats = self.retrive("SELECT elo, wins_1v1, wins_2v2, wins_3v3, losses_1v1, losses_2v2, losses_3v3, team_elo, matches FROM player WHERE discord_id={}".format(member.id))
        if member_stats:
            #embed = discord.Embed(title ="{}".format(member.name), description="**Solo Rating:** {} \n **Team Rating:** {} \n **Matches:** {}".format(member_stats[0], member_stats[7], member_stats[8]), colour = aqua)
            #embed.add_field(name='1v1 Wins', value=member_stats[1], inline=True)
            embed = discord.Embed(title ="{}".format(member.name), description="**Rating:** {} \n **Matches:** {}".format(member_stats[7], member_stats[8]), colour = aqua)
            embed.add_field(name='2v2 Wins', value=member_stats[2], inline=True)
            embed.add_field(name='3v3 Wins', value=member_stats[3], inline=True)
            #embed.add_field(name='1v1 Losses', value=member_stats[4], inline=True)
            embed.add_field(name=' ', value="", inline=True)
            embed.add_field(name='2v2 Losses', value=member_stats[5], inline=True)
            embed.add_field(name='3v3 Losses', value=member_stats[6], inline=True)
            embed.add_field(name=' ', value="", inline=True)
            embed.set_thumbnail(url=member.avatar)
            await interaction.response.defer()
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message("Player not found", ephemeral=True)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlogs(self, ctx):
        channel_id = ctx.channel.id
        self.insert("UPDATE config SET value={} WHERE variable='LOG_CHANNEL'".format(channel_id))
        self.cards_channel = channel_id
        await ctx.send("This channel has been set as the log channel")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx):
        self.queue_messages['1v1'] = self.retrive("SELECT value FROM config WHERE variable='1V1_MESSAGE'")[0]
        self.queue_messages['2v2'] = self.retrive("SELECT value FROM config WHERE variable='2V2_MESSAGE'")[0]
        self.queue_messages['3v3'] = self.retrive("SELECT value FROM config WHERE variable='3V3_MESSAGE'")[0]
        self.log_channel = self.retrive("SELECT value FROM config WHERE variable='LOG_CHANNEL'")[0]
        self.log_channel = self.bot.get_channel(int(self.log_channel))
        self.cards_channel = self.retrive("SELECT value FROM config WHERE variable='CARD_CHANNEL'")[0]
        self.cards_channel = self.bot.get_channel(int(self.cards_channel))
        await ctx.send("DB reloaded")

async def setup(bot):
    await bot.add_cog(matchmaking(bot))
