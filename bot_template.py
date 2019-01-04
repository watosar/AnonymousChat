# -*- coding: utf-8 -*-

import AnonymousChat
import asyncio
import logging

asyncio.set_event_loop(asyncio.new_event_loop())
logging.basicConfig(level=logging.INFO)

token = 'hogehoge'

client = AnonymousChat.Client(
  mount_general_system_channel = True,
  ex_system_channels_info = [
    {
      'name': name, 
      'topick':'for AnonyousChatBot <@...>' 
    } for name in ['count','logging','timer']
  ]
)

welcome_message = '''
WELCOME!!
Please read this
・ hogehoge...

all of past logs are here : https://hogehoge
'''

@client.event
async def on_anonc_ready()
  game = discord.Game(name=f'{len(client.member)}人')
  await client.change_presence(game=game)
  await client.owner.send('I\'m ready')
  #task = [channel.sens('I\'m ready') for channel in client.chat_channels]
  #await asyncio.wait(task)
  
@client.event
async def on_anonc_server_register(server):
  invite = await server.channels[0].create_invite()
  await client.owner.send(f'new server registered : {invite.url}')
  
@client.event
async def before_anonc_member_register(member): 
  # member can't receives anonc message, yet
  channel = member.channel
  message = await channel.send(welcome_message)
  await message.pin()
  await channel.send(f'↓↓ latest {min([5,client.count])} messages ↓↓')
  async for log in client.guild.logging_channel.history(limit=5):
    await channel.anonc_send(AnonymousChat.AnoncMessage(log))
  await channel.sens('-----------------------')
  
@client.event
async def on_anonc_member_register(member): 
  # member can receives anonc message
  game = discord.Game(name=f'{len(client.member)}人')
  await client.change_presence(game=game)
  
@client.event
async def should_transfer_anonc_message(message):
  if message.type == discord.MessageType.default:
    content = message.content()
    result = await run_private_command(message)
    if result is True:
      return False
    else:
      return True
  else:
    return False
  
@client.event
async def on_dmessage(message):
  pass
    
@client.event
async def on_anonc_message(message):
  await run_public_command(message)
  await update_log(message)

import random
import string

def random_strring(len_):
  return ''.join(
    random.choice(string.ascii_letters+string.digits) 
    for i in range(len_)
    )
  
@client.event
async def on_message_at_timer_channel(message):
    await asyncio.wait([role.edit(name=random_string(8)) for role in client.guild.roles])

async def update_log(message):
  ...
  
@client.event
async def get_count():
  async for i in  self.guild.count_channel.history(limit=1):
    return int(i.count)
 
@client.event
async def on_count_update():
  await client.count_channel.send(client.count)

client.run(token)
