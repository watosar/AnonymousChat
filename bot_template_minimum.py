# -*- coding: utf-8 -*-

import anonchat
import os

token = os.environ['token']
client = anonchat.AnoncBaseClient()


@client.event
async def on_anonc_ready():
    for g in client.guilds and g == client.anonc_guild.anonc_system_guild and client.bot_owner not in g.members:
        invite = (await g.invites())[0]
        print(f'you should join here {invite}')
        
        
client.run(token)
