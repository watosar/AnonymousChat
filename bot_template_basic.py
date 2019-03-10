# -*- coding: utf-8 -*-

import anonchat
import discord
import asyncio
import logging
import json
from collections import namedtuple
from textwrap import dedent
import os
from io import BytesIO

asyncio.set_event_loop(asyncio.new_event_loop())
logging.basicConfig(level=logging.INFO)

token = os.environ['token']

welcome_message = '''
{member.mention}
WELCOME !!
This is Anonymous Chat by nekojyarasi#9236
'''


client = anonchat.AnoncBaseClient(
    use_default_system_channel=True,
    anonc_system_channels_info=[
      {
        'name': name,
        'topic': 'for AnonyousChatBot'
      } for name in ['count', 'history', 'timer']
    ],
    nsfw=True,
    with_role=True,
    show_chat_id=True,
    default_name='名無し'
)


async def update_presence():
    game = discord.Game(name=f'{len(client.anonc_guild.anonc_chat_channels)}人')
    await client.change_presence(activity=game)
    
    
async def send_to_bot_owner(content):
    print(content)
    try:
        await client.bot_owner.send(content)
    except discord.errors.Forbidden as e:
        print('Exception', e)


def message_to_html_style(message):
    msg = webhook_info_message_to_message_obj(message)
    return dedent(f'''\
    <p>
    {msg.author.name}&nbsp;&nbsp;<font color="#acadaf">{str(msg.created_at).split('.')[0]}</font><br>
    &nbsp;&nbsp;&nbsp;{msg.content.replace(chr(10),'<br>&nbsp;&nbsp;&nbsp;')}
    </p>
    ''')

async def make_history_html_file():
    base = ''
    with open('./data/logfile-template.html.txt', encoding='utf-8') as f:
        base = f.read()
    channel = client.anonc_guild.anonc_system_history_channel
    messages = []
    history_to = None
    async for msg in channel.history(limit=1000):
        if not history_to:
            history_to = str(msg.created_at.date())
        messages.append(message_to_html_style(msg))
    else:
        history_from = str(msg.created_at.date())
    f = discord.File(
        BytesIO(
            bytearray(
                base.format(
                    history_from=history_from,
                    history_to=history_to,
                    messages=''.join(reversed(messages))
                ).replace(':msg_anchor:', '>>').replace(':at_sign:', '@').replace('[', '{').replace(']', '}'),
                'utf-8'
            )
        ),
        filename='logfile.html'
    )
    return f
     

@client.event
async def on_anonc_ready():
    await update_presence()
    await send_to_bot_owner('I’m ready')
    print('member guilds')
    for g in client.guilds:
        print(f'{g.name}:{len(g.members)}members')
        if g == client.anonc_guild.anonc_system_guild and client.bot_owner not in g.members:
            invite = (await g.invites())[0]
            print(f'you should join here {invite}')


@client.event
async def init_anonc_count():
    ch = client.anonc_guild.anonc_system_count_channel
    async for m in ch.history(limit=1):
        return int(m.content)
    else:
        return 0
        

@client.event
async def on_anonc_count_update(value):
    await client.anonc_guild.anonc_system_count_channel.send(value)
        
  
@client.event
async def on_anonc_message(anonc_message):
    # await run_public_command(message)
    await client.anonc_guild.anonc_system_history_channel.send(anonc_message.to_dict())
  
  
@client.event
async def on_direct_message(message):
    if message.author == client.user:
        return
    await send_to_bot_owner(f'__message from {message.author}__\n{message.content}')
    if message.author == client.bot_owner and message.content == 'close':
        await client.logout()
        client.loop.close()
  
  
@client.event
async def on_message_at_timer_channel(message):
    print(f'reset anonc id : {message.content}')
    await client.anonc_guild.reset_all_anonc_id()
    await send_to_bot_owner('anonc id reseted')
    

@client.event
async def on_message_at_general_channel(message):
    if message.author == client.user:
        return
    content = message.content
    print('general :', content)
    if content == 'change id present':
        client.show_chat_id = not client.show_chat_id
        await message.channel.send(f'now show chat id is {client.show_chat_id}')
    elif content == 'close':
        await client.logout()
        client.loop.close()
    elif content == 'log':
        await message.channel.send(file=await make_history_html_file())
        
        
@client.event
async def on_anonc_member_guild_created(guild):
    print('new guild created', guild)
    msg = await guild.system_channel.send('hello')
    invite = await msg.channel.create_invite()
    await send_to_bot_owner(f'registered new server : {invite.url}')
    anonc_system_guild = client.anonc_guild.anonc_system_guild
    if anonc_system_guild:
        await anonc_system_guild.system_channel.send(f'registered new server : {invite.url}')
    elif guild.name.split('-')[-1] == '0':
        await guild.system_channel.send(f'registered new server : {invite.url}')
        
        
@client.event
async def on_anonc_member_join(anonc_chat_channel):
    message = await anonc_chat_channel.send(welcome_message.format(member=anonc_chat_channel.anonc_member))
    await message.pin()
    await update_presence()
    client.loop.create_task(anonc_chat_channel.send(file=make_history_html_file()))

@client.event
async def on_anonc_member_removed(member):
    await update_presence()
  
  
def webhook_info_message_to_message_obj(message):
    info_dict = json.loads(message.content.replace("'", '"'))
    msg = anonchat.utils.get_discord_message_mimicked(content=info_dict['content'], author_name=info_dict['username'], created_at=message.created_at)
    return msg
 
 
@client.event
async def get_message_numbered(num):
    channel = client.anonc_guild.anonc_system_history_channel
    loop_limit = client.anonc_count - num
    async for message in channel.history(limit=loop_limit):
        pass
    msg = webhook_info_message_to_message_obj(message)
    if int(msg.author.name.split(':')[0]) == num:
        return msg
    else:
        raise ValueError(message.content)
    
    
client.run(token)

