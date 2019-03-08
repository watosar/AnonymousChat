# -*- coding: utf-8 -*-

from aiohttp import request as aiohttp_request


class AnoncChannel:
    """
    to manage AnonChat member | chat_id | role | message sending
    """
    
    __slots__ = ('_core', 'anonc_webhook', 'anonc_member', 'anonc_id_role', 'anonc_id')
    
    def __init__(self, channel, anonc_webhook, anonc_member=None, anonc_id_role=None, anonc_id=None):
        self._core = channel
        self.anonc_webhook = anonc_webhook
        self.anonc_member = anonc_member or channel.guild.get_member(int(anonc_webhook.name))
        self.anonc_id_role = anonc_id_role
        self.anonc_id = channel.topic
    
    def __getattr__(self, key):
        if key in self.__slots__:
            return getattr(self, key)
        else:
            return getattr(self._core, key)
      
    def __eq__(self, other):
        return self._core == other
    
    def is_equal_to(self, channel):
        return self.__eq__(channel)
    
    async def anonc_send(self, anonc_message):
        headers = {'User-Agent': 'DiscordBot', 'Content-Type': 'application/json'}
        async with aiohttp_request('POST', self.anonc_webhook.url, headers=headers, json=anonc_message.to_dict(self)) as session:
            return
    
    async def edit(self, **kwargs):
        if 'topic' in kwargs:
            self.anonc_id = kwargs['topick']
        await self._core.edit(**kwargs)
