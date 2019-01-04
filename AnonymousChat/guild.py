# -*- coding: utf-8 -*-

import discord
import asyncio

'''
役職振り分け廃止 → 権限無くとも全役職およびそのメンバーを閲覧可能
チャンネルトピックにroleid？
'''


class AnoncGuild:
  def __init__(self, client, *, mount_general_system_channel =True,system_channels_info = [{}]):
    self.client = client
    self.loop = client.loop
    self.servers = []
    self.categories = []
    self.channels = []
    self.roles = []
    self.mount_general_system_channel = mount_general_system_channel
    self.system_channels_info = system_channels_info
    self._tmp = []
    self.system_channels = []
    
  @property
  def members(self):
    return [i.member for i in self.chat_channels]
    
  @property
  def chat_channels(self):
    return [i for i in self.channels if i not in self.system_channels]
  
  def anonc_get_role(self, role_id):
    for i in servers:
      role = i.get_role(role_id)
      if role:
        return role
    return None
    
  def anonc_get_channel(self, member):
    return next(
      channel for channel in self.chat_channels
      if channel.anonc_member == member
      )
    
  async def startup(self):
    await self.setup()
  
  async def setup(self):
    for _channel in await self.client.get_all_channels():
      if self.setup_system_channel(_channel):
        pass
      elif await self.is_anonc_channel(_channel):
        channel = await self.cast_to_AnoncChannel(_channel)
        self.channels.append(channel)
        if channel.guild not in self.servers:
          self.servers.append(channel.guild)
        if channel.category not in self.categories:
          self.categories.append(channel.category)
    else:
      pass
            
    if not self.channels:
      await self.register_new_server()
      
    if len(self.sytem_channels_info)!=len(self.system_channels):
      for i in (i for i in self.system_channels_info if id(i)not in self._tmp):
        server = await self.get_available_server()
        channel = await server.create_text_channel(**i)
        self.system_channels.append(channel)
      del self._tmp, self.system_channels_info
      
    
  def setup_system_channel(self, channel):
    if not self.system_channels_info[0]:
      return False
    
    for channel_info in self.system_channels_info:
      if self.mount_general_system_channel \
         and channel == channel.guild.system_channel \
         and channel.name == 'general':
        self.system_channels.append(channel)
        return True
      elif all(getattr(channel,key) == value for key, value in channel_info.items()):
        if id(channel_info) not in self._tmp:
          self._tmp.append(id(channel_info))
          setattr(self,f'{channel_info["name"]}_channel',channel)
          self.system_channels.append(channel)
          return True
        else:
          raise ValueError(f'not one channels matche to {channel_info}')
    else:
      return False
          
  async def is_anonc_channel(self, channel):
    if await self.has_anonc_webhook(channel):
      return True
    else:
      return False
    
  async def has_anonc_webhook(self, channel):
    for i in await channel.webhooks():
      if i.user == self.client.user:
        return True
    else:
      return False
    
  async def cast_to_AnoncChannel(self, channel):
    for webhook in await channel.webhooks():
      if webhook.user == self.client.user:
        break
    else:
      raise ValueError('failed to find webhook')
    
    return AnoncChannel(channel, webhook)
    
  async def register_new_anonc_server(): # fier client.on_guild_join 
    server = self.client.create_guild(f'AnonymousChatServer-{len(self.servers)+1}')
    await server.default_role.edit(
      mantionable = self.can_mention_everyone,
      permissions = discord.Permissions.none()
      )
    bot_owner = await server.create_role(
      name='bot owner',
      permissions = discord.Permissions.all()
      )
    for channel in server.channels:
      if not(self.mount_general_system_channel) or not isinstance(channel,(discord.TextChannel,)):
        await channel.delete()
      else:
        await channel.edit(
          bot_owner, 
          read_messages=True,
          send_messages=True
        )
        self.system_channels.append(channel)
    self.servers.append(server)
    return server
    
  async def register_new_anonc_member(self, member):
    role = await self.register_new_anonc_role()
    channel = await self.register_new_anonc_channel(member,role)
    await self.client.on_anonc_channel_register(channel)
    self.members.append(member)
    return member
    
  async def register_new_anonc_channel(self, member, role):
    available_server = self.get_available_server()
    if available_server is None:
      available_server = await self.register_new_server()
      
    available_category = max(
      (cate for cate in self.categories 
      if cate.guild == available_server and len(cate.channels)<50),
      key = lambda cate:len(cate.channels),
      default = None
      )
    txc_base_overwrites = {
      server.default_role: discord.PermissionOverwrite(read_messages=False),
      member: discord.PermissionOverwrite(read_messages=True,send_messages=True,manage_messages=True,attach_files=True,read_message_history=True)
    }
    
    if available_category is None:
      available_category = await available_server.create_category_channel(
          name = f'category-{len(self.categories)+1}',
          overwrites = {available_server.default_role:
            discord.PermissionOverwrite(read_messages=False)}
        )
      self.categories.append(category)
      
    channel = await available_server.create_text_channel(
      name = member.name,
      overwrites=txc_base_overwrites,
      category = available_category
      )
      
    
    webhook = await channel.create_webhook(
      name=f'{base36(member.id)}:{base36(role.id)}')
    
    self.channels.append(AnoncChannel(channel, webhook, member, role))
    return channel

base36 = lambda num: ''.join('0123456789abcdefghijklmnopqrstuvwxyz'[i] for i in reversed([(digit or loop.close(),) and digit for next,loop in [(num,(_ for _ in iter(int,None)))]for _ in loop for next, digit in [divmod(next,36)]]))
