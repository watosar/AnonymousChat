# -*- coding: utf-8 -*-

import discord
import asyncio
from .utils import base36encode
from .channel import AnoncChannel

'''
役職振り分け廃止 → 権限無くとも全役職およびそのメンバーを閲覧可能
チャンネルトピックにroleid？
'''


class AnoncGuild:

    def __init__(self, client, *, mount_general_system_channel=True, ex_system_channels_info=[{}]):
        self.client = client
        self.loop = client.loop
        self.servers = []
        self.categories = []
        self.channels = []
        self.roles = []
        self.mount_general_system_channel = mount_general_system_channel
        self.system_channels_info = ex_system_channels_info
        self._tmp = []
        self.system_channels = []
        self.present_id = False
        self.arrow_handle_name = True

    @property
    def members(self):
        return [i.member for i in self.chat_channels]

    @property
    def chat_channels(self):
        return [i for i in self.channels if i not in self.system_channels]

    def anonc_get_role(self, role_id):
        for i in self.servers:
            role = i.get_role(role_id)
            if role:
                return role
        return None

    def anonc_get_channel(self, member):
        return next(
            channel for channel in self.chat_channels
            if channel.anonc_member == member
        )

    async def get_anonc_emojis(self, key):
        pass

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

        if len(self.sytem_channels_info) != len(self.system_channels):
            for i in (i for i in self.system_channels_info if id(i) not in self._tmp):
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
            elif all(getattr(channel, key) == value for key, value in channel_info.items()):
                if id(channel_info) not in self._tmp:
                    self._tmp.append(id(channel_info))
                    setattr(self, f'{channel_info["name"]}_channel', channel)
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

    async def register_new_anonc_server(self):  # fier client.on_guild_join
        server = self.anonc_client.create_guild(f'AnonymousChatServer-{len(self.servers)+1}')
        await server.default_role.edit(
            mantionable=False,
            permissions=discord.Permissions.none()
        )
        bot_owner = await server.create_role(
            name='bot owner',
            permissions=discord.Permissions.all()
        )
        for channel in server.channels:
            if not (self.mount_general_system_channel) or not isinstance(channel, (discord.TextChannel,)):
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
        channel = await self.register_new_anonc_channel(member, role)
        await self.client.on_anonc_channel_register(channel)
        self.members.append(member)
        return member

    async def register_new_anonc_channel(self, member, role):
        available_server = self.get_available_server()
        if available_server is None:
            available_server = await self.register_new_server()

        available_category = max(
            (cate for cate in self.categories
             if cate.guild == available_server and len(cate.channels) < 50),
            key=lambda cate: len(cate.channels),
            default=None
        )
        txc_base_overwrites = {
            available_server.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True,
                                                attach_files=True, read_message_history=True)
        }

        if available_category is None:
            available_category = await available_server.create_category_channel(
                name=f'category-{len(self.categories)+1}',
                overwrites={available_server.default_role: discord.PermissionOverwrite(read_messages=False)}
            )
            self.categories.append(available_category)

        channel = await available_server.create_text_channel(
            name=member.name,
            overwrites=txc_base_overwrites,
            category=available_category
        )

        webhook = await channel.create_webhook(
            name=f'{base36encode(member.id)}:{base36encode(role.id)}')

        self.channels.append(AnoncChannel(channel, webhook, member, role))
        return channel

    async def reset_anonc_roles(self):
        async def reset_anonc_role(channel):
            role = channel.guild.get_role(channel.anonc_webhook.name.split(':')[1])
            await role.delete()
            self.roles.remove(role)
            role = await self.register_new_anonc_role()
            await channel.anonc_webhook.edit(name=f'{base36encode(channel.member.id)}:{base36encode(role.id)}')

        await asyncio.wait([reset_anonc_role(channel) for channel in self.chat_channels])
