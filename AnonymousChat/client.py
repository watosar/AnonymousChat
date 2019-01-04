# -*- coding: utf-8 -*-

import discord
import asyncio
from collections import deque

class AnoncBaseClient(discord.Client):
  def __init__(self,*args,**kwargs):
    super().__init__(*args,**kwargs)
    
    self.number_of_channel_stock= 0
    self.channel_stock = deque()
    self.queue = asyncio.Queue(loop=self.loop)
    
    self.anonc_guild = AnoncGuild(
      self,
      mount_general_system_channel = kwargs.get(
        'mount_general_system_channel', True),
      ex_system_channels_info=kwargs.get(
        'ex_system_channels_info', None)
      )
      
    self.anonc_message_base = AnoncMessageBase(
      max_ancheralbe_number = -1 #-1 なら無限
      )
    
    self.message_queue = []
    self.message_queue_update = asyncio.Event(loop=self.loop)
    self.anonc_ready = asyncio.Event(loop=self.loop)

  async def on_ready(self):
    print('start on_ready tasks')
    self.bot_owner = [await self.application_info()][0].owner
    await self.anonc_guild.startup()
    self.count = await self.init_count()
    
    for channel in self.anonc_guild.chat_channels:
      self.create_task_to_transfer_message_for_channel(channel)
    
    
    self.anonc_ready.set()
    await self.on_anonc_ready()
    
  async def init_count():
    return 0

  async def on_anonc_ready(self):
    pass 


  async def on_message(self, message):
    if not self.anonc_ready.is_set():
      await self.anonc_ready.wait()
    channel = message.channel
    if isinstance(channel, (discord.DMChannel,)):
      await self.on_dm_message(message)
    elif channel in self.guild.chat_channels:
      if self.is_loopback_message(message):
        return
      if await self.should_transfer_anonc_message(message):
        self.put_message_in_transfer_queues(message) #make bg_task
        self.count += 1
        await asyncio.wait([self.on_anonc_message(AnoncMessage(message)),self.on_count_update()])
      else:
        return
    elif channel in self.guild.system_channels:
      on_message_at_some_channel = getattr(self,f'on_message_at_{channel.name}_channel',None)
      if method:
        await on_message_at_some_channel(message)
    else:
      pass

    return

  def is_loopback_message(self, message):
    if getattr(message,'webhook_id',None):
      True
    else:
      False

  async def should_transfer_anonc_message(self, message):
    if message.type == discord.MessageType.default:
      return True
    else:
      return False
  
  async def before_transfer_anonc_message(self, anonc_message, anonc_channel):
    await anonc_mesaage.adupt_for(channel)
    for ancher in anonc_mesaage.anchers:
      if ancher<=self.count:
        anchered_message = await self.get_numbered_message(ancher)
        embed=discord.Embed(description=anchered_message.content)
        embed.set_author(name=anchered_message.author.name)
        anonc_mesaage.embeds.append(embed)
    return anonc_message
    
    
  async def get_numbered_message(self, number):
    class imitate_message:
      content='...'
      class author:
        name = f'{count}:名無し'
    return imitate_message()


  def put_message_in_transfer_queues(self, message):
    for task in self.running_transfer_tasks:
      task.queue.put_nowait(message)
  
  
  def create_task_to_transfer_message_for_channel(self, channel):
    async def task_for_channel(channel):
      while not self.is_closed():
        anonc_message = AnoncMessage(await task_for_channel.queue.get())
        anonc_message = await self.before_transfer_anonc_message(anonc_message, channel)
        channel.anonc_webhook.send(
          **anonc_message.to_dict()
          )
    task_for_channel.queue= asyncio.Queue()
    self.loop.create_task(task_for_channel(channel))
    self.running_transfer_task.append(task_for_channel)
  

  async def on_dm_message(self, message):
    pass

  async def on_message_at_system_channels(self, message):
    pass

  async def on_anonc_message(self, message):
    pass

  async def on_anonc_channel_register(self, channel):
    self.create_task_to_transfer_message_for_channel(channel)

  async def on_member_join(self, member):
    if not self.anonc_ready.is_set():
      await self.anonc_ready.wait()

    if self.should_anonc_member_register(member):
      if self.stack_channels:
        channel = self.stack_channels.popleft()
      else:
        channel=None

      #member = AnoncMember(member, channel)
      await self.before_anonc_member_register(member)
      await self.guild.register_new_member(member)
      await self.on_anonc_member_register(member)

  def should_anonc_member_register(self, member):
    return True

  async def before_anonc_member_register(self, member):
    pass

  async def on_anonc_member_register(self, member):
    pass


  async def on_member_remove(self, member):
    if not self.anonc_ready.is_set():
      await self.anonc_ready.wait()

    member = self.chat_group.get(member)
    if not member:
      return

    await member.removed()
    await self.on_anonc_member_removed(member)
    return


  async def on_anonc_member_removed(self, member):
    pass

  async def on_guild_join(self, server):
    if server.owner == server.me:
      await on_anonc_server_register(server)
    else:
      await self.bot_owner.send('joined suspicious server\nname: {server.name}, id: {server.id}')
      for channel in server.channels:
        try:
          invite = [await channel.invites()][0]
          break
        except discord.Forbidden as e:
          print(e.response)
        try:
          invite = await channel.create_invite()
          break
        except discord.HTTPException as e:
          print(e.response)
      else:
        await self.bot_owner.send('failed to get invite')
        return 
      await self.bot_owner.send(f'invite: {invite.url}')
  
  async def on_anonc_server_register(self, server):
    invite = await server.channels[0].create_invite()
    await self.bot_owner.send(f'registered new server : {invite.url}')
