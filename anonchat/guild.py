# -*- coding: utf-8 -*-

from discord import TextChannel, CategoryChannel, Guild, Permissions, PermissionOverwrite
from .channel import AnoncChannel
from .utils import base36encode, random_string
from typing import Optional,List
import re

'''
while guild is single
    can use role
'''


anonc_id_pat = re.compile('[a-zA-Z]{4}')


class AnoncIntegrationGuild:
    """
    manage AnonChat member guilds | channels
    """
    
    def __init__(self, client, nsfw, channel_limit=500):
        self.client = client
        
        self.nsfw = nsfw
        
        self._anonc_system_guild_core = None
        
        self.channel_limit = channel_limit
        self.anonc_chat_channels = []
        self.anonc_system_channels = []
        self.anonc_chat_id_roles = []
    
    @property
    def anonc_system_guild(self):
        return next((g for g in self.client.guilds if g==self._anonc_system_guild_core),None)
    
    @anonc_system_guild.setter
    def anonc_system_guild(self, guild):
        self._anonc_system_guild_core = guild
        
    @property
    def anonc_guilds(self) -> List[Guild]:
      return [g for g in self.client.guilds if g != self.anonc_system_guild]
  
    async def setup(self, use_defo_sys_ch=False, anonc_sys_chs_info=[{}]) -> None:
      
        sys_chs_cache=[]
        def _is_anonc_sys_ch(_ch) -> bool:
            if use_defo_sys_ch:
                if _ch == _ch.guild.system_channel:
                    return True
            for i in anonc_sys_chs_info:
                if not i:
                    return False
                if all(getattr(_ch, k)==v for k, v in i.items()):
                    sys_chs_cache.append(i)
                    return True
            return False
          
        for g in self.anonc_guilds:
            if g.owner != self.client.user:
                await g.leave()
                print(f'left {g}')
            elif g.name==f'AnonChat[{base36encode(self.client.user.id)}]-0':
                self.anonc_system_guild = g
              
        if not self.anonc_system_guild:
            self.anonc_system_guild = await self._create_anonc_system_guild()
      
        guild_count = len(self.anonc_guilds)
        if not guild_count:
            await self._create_new_anonc_member_guild()
        elif self.client.with_role and guild_count>1:
            print('You cannot be with_role as True\nToggle flg to False')
            self.client.with_role = False
      
        for ch in self.client.get_all_channels():
            if not isinstance(ch,(TextChannel,)):
                continue
        
            if _is_anonc_sys_ch(ch):
                self.anonc_system_channels.append(ch)
        
            if not self.get_anonc_chat_channel_from_channel(ch):
                anon_ch = await self.cast_to_anonc_chat_channel(ch)
                if anon_ch:
                    self.anonc_chat_channels.append(anon_ch)
      
        for left_sys_ch_info in (ch for ch in anonc_sys_chs_info if ch not in sys_chs_cache):
            if not left_sys_ch_info:
                return 
            channel = await self.anonc_system_guild.create_text_channel(
                name=left_sys_ch_info.pop('name', 'anonc_sys'),
                **left_sys_ch_info
            )
            self.anonc_system_channels.append(channel)
          
        self._set_snonc_system_channels_to_attr()
  
    def _set_snonc_system_channels_to_attr(self):
        for ch in self.anonc_system_channels:
            name = f'anonc_system_{ch.name}_channel'
            if ch.name=='general' or getattr(self, name, None):
                continue
            setattr(self, name, ch)
            print(name)
        
    async def _create_anonc_system_guild(self) -> Guild:
        guild = await self.client.create_guild(name=f'AnonChat[{base36encode(self.client.user.id)}]-0')
        bot_owner = await guild.create_role(
            name='bot owner',
            permissions=Permissions.all()
        )
        return guild
        
    async def _create_new_anonc_member_guild(self) -> Guild:
        guild = await self.client.create_guild(name=f'AnonChat[{base36encode(self.client.user.id)}]-{len(self.anonc_guilds)+1}')
        
        await guild.default_role.edit(
            mantionable=False,
            permissions=Permissions.none()
        )
        bot_owner = await guild.create_role(
            name='bot owner',
            permissions=Permissions.all()
        )
        anonc_admin = await guild.create_role(
            name='anonc admin',
            permissions=Permissions.none()
        )
        anonc_system = await guild.create_role(
            name='anonc system',
            permissions=Permissions.none()
        )
        
        for name,path in (('msg_anchor',self.client.anchor_emoji_path), ('at_sign',self.client.at_sign_emoji_path)):
            with open(path, 'rb') as f:
                await guild.create_custom_emoji(name=name,image=f.read(),roles=[anonc_system])
        
        for channel in guild.channels:
            if isinstance(channel,(CategoryChannel,)):
                continue
            elif isinstance((channel,(TextChannel,))):
                await channel.category.edit(name='anonc_system_channels')
                await channel.category.set_permission(guild.default_role, read_messages=False)
                await channel.category.set_permission(bot_owner, read_messages=True, send_messages=True)
                await channel.category.set_permission(anonc_admin, read_messages=True, send_messages=True)
            else:
                await channel.category.delete()
                await channel.dleete()
        
        return guild
        
    async def cast_to_anonc_chat_channel(self, channel) -> Optional[AnoncChannel]:
        webhooks = await channel.webhooks()
        for w in webhooks:
            if w.user == self.client.user and w.name.isdigit() and anonc_id_pat.fullmatch(channel.topic):
                anonc_id_role = None
                if self.client.with_role:
                    anonc_id_role = next((r for r in channel.guild.roles if r.name==channel.topic),None)# or await channel.guild.create_role(name=channel.topic)
                    if not anonc_id_role:
                        continue
                return AnoncChannel(channel, w, anonc_id_role=anonc_id_role)
    
    def get_anonc_system_guild_emoji_named(self, name) -> Optional[AnoncChannel]:
        return next((e for e in self.anonc_system_guild.emojis if e.name==name),None)

    def get_anonc_chat_channel_from_channel(self, channel) -> Optional[AnoncChannel]:
        return next((c for c in self.anonc_chat_channels if c.id==channel.id), None)
            
    def get_anonc_chat_channel_from_anonc_id_role_id(self, anonc_id_role_id) -> Optional[AnoncChannel]:
        return next((ch for ch in self.anonc_chat_channels if ch.anonc_id_role and ch.anonc_id_role.id==anonc_id_role_id),None)
    
    def get_anonc_chat_channel_from_anonc_id(self, anonc_id):
        return next((ch for ch in self.anonc_chat_channels if ch.anonc_id==anonc_id),None)
        
    def get_anonc_chat_channel_from_user(self, user):
        return next((ch for ch in self.anonc_chat_channels if ch.anonc_member==user),None)

    async def register_member(self, member):
        for g in sorted(self.anonc_guilds,key=lambda g: len(g.channels),reverse=True):
            if len(g.channels)>=self.channel_limit:
                continue
            break
        else:
            g = await self._create_new_anonc_member_guild()
        
        anonc_ch = await self._create_anonc_chat_channel(g, member)
        self.anonc_chat_channels.append(anonc_ch)
        return anonc_ch
    
    async def _create_anonc_chat_channel(self, guild, member) -> AnoncChannel:
        overwrites = {
            guild.default_role: PermissionOverwrite.from_pair(
                    Permissions.none(), # allow
                    Permissions.all() # deny
                ),
            member: PermissionOverwrite(
                    send_messages = True,
                    read_messages = True,
                    manage_messages = True,
                    attach_files = True,
                    read_message_history = True
                )
        }
        
        anonc_id = random_string(4)
        while self.get_anonc_chat_channel_from_anonc_id(anonc_id):
            anonc_id = random_string(4)
        
        anonc_id_role = None
        if self.client.with_role:
            anonc_id_role = await guild.create_role(name=anonc_id, mentionable=True)
        
        channel = await guild.create_text_channel('anon chat', overwrites=overwrites, topic=anonc_id, nsfw=self.nsfw)
        webhook = await channel.create_webhook(name=str(member.id))
        
        return AnoncChannel(channel, webhook, member, anonc_id_role)
        
    async def reset_all_anonc_id(self):
        for ch in self.anonc_chat_channels:
            new_anonc_id = random_string(4)
            while self.get_anonc_chat_channel_from_anonc_id(new_anonc_id):
                new_anonc_id = random_string(4)
            
            await ch.edit(topic=new_anonc_id)
            if ch.anonc_id_role:
                await ch.anonc_id_role.delete()
                ch.anonc_id_role = await ch.guild.create_role(name=new_anonc_id, mentionable=True)
    
    async def delete_all_anonc_id_role(self):
        pass
    
    async def unregister_member(self, member):
        anonc_chat_channel = self.get_anonc_chat_channel_from_user(member)
        self.anonc_chat_channels.remove(anonc_chat_channel)
        await anonc_chat_channel.delete()
        del anonc_chat_channel

