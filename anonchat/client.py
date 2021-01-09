# -*- coding: utf-8 -*-

import asyncio
from discord import Client, Guild, DMChannel, Message, MessageType, AuditLogAction, Intents
from .guild import AnoncIntegrationGuild
from .message import AnoncMessageMaker
import typing
from pathlib import Path
from collections import namedtuple
import re
import aiohttp

class AnoncCount:
    """
    AnonChat Count descriptor
    """
    def __get__(self, obj, objtype=None) -> int:
        return obj.__dict__.get('anonc_count',0)
        
    def __set__(self, obj, value):
        obj.__dict__['anonc_count']=value
        obj.loop.create_task(obj.on_anonc_count_update(value))


class AnoncBaseClient(Client):
    """
    AnonChat Client
    """
    
    anonc_count = AnoncCount()
    
    def __init__(
      self, *args, anchor_emoji_path=None, at_sign_emoji_path=None, use_default_system_channel=False, anonc_system_channels_info =[{}], nsfw=False, anchorable_limit=None, use_role=True, show_chat_id=True, anonc_default_name='John Doe', guild_base_name='', **kwargs):
        super().__init__(*args, intents=Intents.all(), **kwargs)

        # TODO : add this
        #   self.number_of_channel_stock = 0
        #   self.channel_stock = deque()
        
        self.anchor_emoji_path = anchor_emoji_path or Path(__file__).parent/'template/msg_anchor.png'
        self.at_sign_emoji_path = at_sign_emoji_path or Path(__file__).parent/'template/at_sign.png'
        
        
        self.anonc_guild = AnoncIntegrationGuild(
            self,
            use_role=use_role,
            nsfw=nsfw,
            channel_limit=300)
        
        self.guild_base_name = guild_base_name
        self.use_default_sys_ch = use_default_system_channel
        self.anonc_sys_chs_info = anonc_system_channels_info
        
        self.show_chat_id = show_chat_id
        
        self.anonc_message_maker = AnoncMessageMaker(self, anonc_default_name)
        self.anchorable_limit = anchorable_limit
        
        self.anonc_ready = asyncio.Event(loop=self.loop)

    async def on_ready(self) -> None:
        # init AnonChat client
        
        print('start on_ready tasks')
        print(f'logged on as {self.user}\nuser_id is {self.user.id}')
        self.bot_owner = (await self.application_info()).owner
        '''if not self.bot_owner.dm_channel:
            await self.bot_owner.create_dm()'''
        await self.anonc_guild.setup(
            base_name = self.guild_base_name,
            use_defo_sys_ch=self.use_default_sys_ch,
            anonc_sys_chs_info=self.anonc_sys_chs_info
        )
        # del self.anonc_sys_chs_info, self.anchor_emoji_path, self.at_sign_emoji_path
        '''
        self.anonc_message_maker.set_emojis(
          **{
            i: self.anonc_guild.get_anonc_system_guild_emoji_named(i) 
            for i in ('msg_anchor','at_sign')
          }
        )
        '''
        self.anonc_count = await self.init_anonc_count()
        
        self.anonc_ready.set()
        await self.on_anonc_ready()

    async def init_anonc_count(self) -> int:
        return 0
        
    async def on_anonc_count_update(self, value) -> None:
        pass

    def wait_until_anonc_ready(function):
        async def decorated(self, *args, **kwargs):
            if not self.anonc_ready.is_set():
                await self.anonc_ready.wait()
            return await function(self, *args, **kwargs)
        return decorated

    async def on_anonc_ready(self) -> None:
        pass

    @wait_until_anonc_ready
    async def on_message(self, message: Message) -> None:
        channel = message.channel
        if isinstance(channel, (DMChannel,)):  # on dm
            print('dm')
            await self.on_direct_message(message)

        elif self.anonc_guild.get_anonc_chat_channel_from_channel(channel):  # on anonc chat
            if not await self._is_message_for_chat(message):
                return
                
            print('anonc chat :', channel)
            
            # TODO : private command
            ...

            anonc_count = self.anonc_count+1
            self.anonc_count+=1
            
            attachments = message.attachments
            if attachments:
                await self.head_request_to_attachments(attachments)
            
            anonc_message = await self.anonc_message_maker.make(message, anonc_count)
            self.loop.create_task(self.anonc_send(anonc_message)).add_done_callback(lambda _:self.loop.create_task(message.delete()))
            self.loop.create_task(self.on_anonc_message(anonc_message))  # for public command etc

        elif channel in self.anonc_guild.anonc_system_channels:  # on anonc system
            print('anonc system :', channel)
            on_message_at_some_channel = getattr(self, f'on_message_at_{channel.name}_channel', None)
            if on_message_at_some_channel:
                await on_message_at_some_channel(message)

        else:
            print('else :', message, message.channel)

        return
    
    async def head_request_to_attachments(self, attachments):
        async def head_request(url):
            async with aiohttp.request('HEAD', url):
                pass
        await asyncio.wait([self.loop.create_task(head_request(a.url)) for a in attachments])

    async def _is_message_for_chat(self, msg: Message) -> bool:
        if getattr(msg, 'webhook_id', None):  # check is self webhook
            return False
        if msg.type != MessageType.default:  # ignore system message like pinned
            return False
        if self.anonc_guild.get_anonc_chat_channel_from_channel(msg.channel).anonc_member != msg.author:
            return False

        return True

    async def on_direct_message(self, message: Message) -> None:
        pass

    async def on_anonc_message(self, anonc_msg) -> None:
        pass

    async def anonc_send(self, anonc_msg) -> None:
        tasks = [self.loop.create_task(anonc_channel.anonc_send(anonc_msg)) for anonc_channel in self.anonc_guild.anonc_chat_channels]
        done, _ = await asyncio.wait(tasks)
        
        

    @wait_until_anonc_ready
    async def on_member_join(self, member) -> None:
        print(f'{member} joined to {member.guild}')
        if member == self.bot_owner:
            await member.add_roles(
                next(i for i in member.guild.roles if i.name=='bot owner')
            )
        
        if await self._should_register_member(member):
            anonc_channel = await self.anonc_guild.register_member(member)
            await self.on_anonc_member_join(anonc_channel)
        else:
            if member != self.bot_owner:
                await member.send('Sorry. You cannot join this AnonChat')
                await member.kick()

    async def _should_register_member(self, member) -> bool:
        if member.guild != self.anonc_guild.anonc_system_guild and not self.anonc_guild.get_anonc_chat_channel_from_user(member):
            if self.anonc_guild.use_role and len(self.anonc_guild.anonc_chat_guilds[0].roles)>249:
                return False
            elif len(self.guilds)>9 and min(len(g.channels) for g in self.anonc_chat_guilds)>=self.anonc_guild.channel_limit:
                return False
            return True
        else:
            return False
        
    async def on_anonc_member_join(self, anonc_channel) -> None:
        pass

    @wait_until_anonc_ready
    async def on_member_remove(self, member) -> None:
        if member == self.user:
            return 
        
        anonc_chat_channel = self.anonc_guild.get_anonc_chat_channel_from_user(member)
        
        if not anonc_chat_channel or anonc_chat_channel.guild != member.guild:
            print(f'{member} has no channel in {member.guild} removed')
            return
        await self.anonc_guild.unregister_member(member)
        await self.on_anonc_member_removed(member)

    async def on_anonc_member_removed(self, member) -> None:
        pass
        
    async def on_guild_join(self, guild: Guild) -> None:
        if guild.owner == guild.me:
            await self.on_anonc_member_guild_created(guild)
        else:
            print(f'joined suspicious server\nname: {guild.name}, id: {guild.id}')
            await guild.leave()
            print('left')
    
    '''
    async def on_guild_update(self, bef, aft):
        print('on guild update')
        if bef.name == aft.name:
            return 
        async for entry in aft.audit_logs(limit=5,action=AuditLogAction.guild_update):
            if entry.target == aft and entry.before.name == bef.name and entry.after.name == aft.name:
                break
        else:
            raise ValueError('not found correct audit log')
        if entry.user == self.user:
            return 
        
        print('name update?')
        if await self.anonc_guild.update_base_name(aft.name, bef):
            print(f'guild base name changed to {aft.name}')'''

    async def on_anonc_member_guild_created(self, guild: Guild) -> None:
        msg = await guild.system_channel.send('hi')
        invite = await msg.channel.create_invite()
        await msg.delete()
        print(f'registered new server : {invite.url}')

    async def get_message_numbered(num: int) -> Message:
        pass

