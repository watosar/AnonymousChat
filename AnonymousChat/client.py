# -*- coding: utf-8 -*-

import discord
import asyncio

from .guild import AnoncGuild
from .message import AnoncMessageMaker


class AnoncBaseClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO : あとで実装しましょうねー
        #   self.number_of_channel_stock = 0
        #   self.channel_stock = deque()

        self.anonc_guild = AnoncGuild(
            self,
            mount_general_system_channel=kwargs.get(
                'mount_general_system_channel', True),
            ex_system_channels_info=kwargs.get(
                'ex_system_channels_info', None)
        )
        self.anonc_message_maker = AnoncMessageMaker(self)

        self.anonc_message_anchor_limit = kwargs.get('anonc_message_anchor_limit', None)
        self.message_queue = []
        self.message_queue_update = asyncio.Event(loop=self.loop)
        self.anonc_ready = asyncio.Event(loop=self.loop)

        self.bot_owner = None
        self.count = None

    async def on_ready(self):
        """
        init AnonC client
        """
        print('start on_ready tasks')
        self.bot_owner = [await self.application_info()][0].owner
        await self.anonc_guild.startup()
        self.count = await self.init_count()

        # prepare for async message sending
        for channel in self.anonc_guild.chat_channels:
            self.create_task_to_transfer_message_for_channel(channel)

        self.anonc_ready.set()
        await self.on_anonc_ready()

    async def init_count(self) -> int:
        return 0

    @staticmethod
    def wait_until_anonc_ready(coroutine):  # decorator
        async def decorated(self, *args, **kwargs):
            if not self.anonc_ready.is_set():
                await self.anonc_ready.wait()
            return await coroutine(self, *args, **kwargs)

        return decorated

    async def on_anonc_ready(self):
        """
        anonc ready task
        :return:
        """
        pass

    @wait_until_anonc_ready
    async def on_message(self, message):
        channel = message.channel
        if isinstance(channel, (discord.DMChannel,)):  # on dm
            await self.on_direct_message(message)

        elif channel in self.guild.chat_channels:  # on anonc chat
            message = await self.message_sieve(message)
            if not message:
                return

            # TODO : private command
            ...

            self.count += 1
            anonc_message = await self.anonc_message_maker.make(message, self.count)
            self.loop.create_task(self.anonc_send(anonc_message))
            self.loop.create_task(self.on_anonc_message(anonc_message))  # for public command

        elif channel in self.anonc_guild.system_channels:  # on anonc system
            on_message_at_some_channel = getattr(self, f'on_message_at_{channel.name}_channel', None)
            if on_message_at_some_channel:
                await on_message_at_some_channel(message)

        else:
            pass

        return

    async def message_sieve(self, msg):
        if not getattr(msg, 'webhook_id', None):  # check is self webhook
            return
        if msg.type != discord.MessageType.default:  # ignore system message like pinned
            return

        return msg

    async def on_direct_message(self, message):
        pass

    async def on_anonc_message(self, anonc_msg):
        pass

    async def anonc_send(self, anonc_msg):
        coroutines = (anonc_channel.send(anonc_msg) for anonc_channel in self.anonc_guild.chat_channels)
        await asyncio.wait([self.loop.create_task(coro) for coro in coroutines])

    async def on_anonc_channel_register(self, channel):
        self.create_task_to_transfer_message_for_channel(channel)

    @wait_until_anonc_ready
    async def on_member_join(self, member):
        if await self.should_register_member(member):
            if self.stack_channels:
                channel = self.stack_channels.popleft()
            else:
                channel = None

            await self.before_member_register(member)
            anonc_member = await self.anonc_guild.register_member(member, channel)
            await self.on_anonc_member_register(anonc_member)

    async def should_register_member(self, member):
        return True

    async def before_member_register(self, member):
        pass

    async def on_anonc_member_register(self, anonc_member):
        pass

    @wait_until_anonc_ready
    async def on_member_remove(self, member):
        anonc_member = self.anonc_guild.get_anonc_member(member)
        if not member:
            return

        await self.anonc_guild.remove(anonc_member)
        await self.on_anonc_member_removed(anonc_member)
        return

    async def on_anonc_member_removed(self, member):
        pass

    async def on_guild_join(self, server):
        if server.owner == server.me:
            await self.on_new_anonc_server_register(server)
        else:
            await self.bot_owner.send('joined suspicious server\nname: {server.name}, id: {server.id}')
            invites = await server.invites()
            if not invites:
                for channel in server.channels:
                    try:
                        invite = await channel.create_invite()
                        break
                    except discord.HTTPException as e:
                        print(e.response)
                else:
                    await self.bot_owner.send('failed to get invite')
                    return
            else:
                invite = invites[0]
            await self.bot_owner.send(f'invite: {invite.url}')

    async def on_new_anonc_server_register(self, server):
        invite = await server.channels[0].create_invite()
        await self.bot_owner.send(f'registered new server : {invite.url}')

    async def send_to_all_chat_channels(self, *args, **kwargs):
        await asyncio.wait([channel.send(*args, **kwargs) for channel in self.anonc_guild.chat_channels])
