# -*- coding: utf-8 -*-

from aiohttp import request as aiohttp_request
from asyncio import sleep
from discord.utils import _parse_ratelimit_header

class AnoncChannel:
    """
    to manage AnonChat member | chat_id | role | message sending
    """
    
    __slots__ = ('_core', 'anonc_webhook', 'anonc_member', 'anonc_id_role', 'anonc_id')
    
    def __init__(self, channel, anonc_webhook, anonc_member=None, anonc_id_role=None, anonc_id=None):
        self._core = channel
        self.anonc_webhook = anonc_webhook
        self.anonc_member = anonc_member or channel.guild.get_member(int(anonc_webhook.name))
        if not self.anonc_member:
            raise ValueError('no member found')
        top_role_name = self.anonc_member.top_role.name
        if top_role_name in ('bot owner', 'anonc moderator'):
            anonc_id = top_role_name.split()[1]
        self.anonc_id_role = anonc_id_role
        self.anonc_id = anonc_id or channel.topic
    
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
        json = anonc_message.to_dict(self)
        for tries in range(2):
            async with aiohttp_request('POST', self.anonc_webhook.url, headers=headers, json=json) as r:             
                # check if we have rate limit header information
                remaining = r.headers.get('X-Ratelimit-Remaining')
                if remaining == '0' and r.status != 429:
                    delta = _parse_ratelimit_header(r)
                    await sleep(delta)
    
                if 300 > r.status >= 200:
                    return r
    
                # we are being rate limited
                if r.status == 429:
                    retry_after = data['retry_after'] / 1000.0
                    await sleep(retry_after)
                    continue
    
                if r.status in (500, 502):
                    await sleep(1 + tries * 2)
                    continue
    
                if r.status == 403:
                    raise Forbidden(r, data)
                elif r.status == 404:
                    raise NotFound(r, data)
                else:
                    raise HTTPException(r, data)
    
    async def edit(self, **kwargs):
        if 'topic' in kwargs:
            new_anonc_id = kwargs['topic']
            if self.anonc_id not in ('owner', 'moderator'):
                self.anonc_id = new_anonc_id
        await self._core.edit(**kwargs)

