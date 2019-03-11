# -*- coding: utf-8 -*-

import re
import typing
from copy import deepcopy

class AnoncMessage:
    """
    AnoncMessage, to be send by AnoncChannel.anonc_send
    """
    def __init__(self, body, count):
        self.body = body
        self.count = count

    def to_dict(self, anonc_channel=None):
        adapted = deepcopy(self.body['general'])
        ext = {}
        if anonc_channel:
            ext = self.body['ext'].get(anonc_channel.anonc_member.id, {})
            anchor_emoji = str(next(i for i in anonc_channel.guild.emojis if i.name == 'msg_anchor'))
            at_sign_emoji = str(next(i for i in anonc_channel.guild.emojis if i.name == 'at_sign'))
            adapted['content'] = adapted['content'].replace(':msg_anchor:', anchor_emoji).replace(':at_sign:', at_sign_emoji)
            for embed in adapted['embeds']:
                if 'description' not in embed:
                    continue
                embed['description'] = embed['description'].replace(':msg_anchor:', anchor_emoji).replace(':at_sign:', at_sign_emoji)
        adapted.update(ext)
        
        adapted['content'] = f'ID:{adapted.pop("anonc_id")}\n{adapted["content"]}'
        adapted['username'] = f'{self.count}:{adapted["username"]}'
        return adapted


class AnoncMessageMaker:
    """
    to make AnoncMessage from discord.Message
    """
    def __init__(self, client, default_name = 'jhon doe'):
        self.client = client
        self.default_name = default_name
        self.anchor_pat = re.compile('(?=(?<=^)|(?<= ))>>([0-9]+)(?= |$)', flags=re.MULTILINE)
        self.mention_pat_role = re.compile('<@&([0-9]+)>', flags=re.MULTILINE)
        self.mention_pat_anonc = re.compile('@(([0-9]+)|([A-Za-z]{4}))', flags=re.MULTILINE)
        self.emojis={'msg_anchor','at_sign'}
    
    
    #def set_emojis(self,msg_anchor,at_sign):
    #    self.emojis['msg_anchor'] = str(msg_anchor)
    #    self.emojis['at_sign'] = str(at_sign)
        
    async def make(self, msg, count) -> AnoncMessage:
        anonc_id = self.client.anonc_guild.get_anonc_chat_channel_from_channel(msg.channel).anonc_id
        evaled_content = await self.eval_content(msg.content, count)
        body = {
            'general':
                {
                    'username': self.default_name,
                    'content': evaled_content['content'].pop('general'),
                    'embeds': [i.to_dict() for i in msg.embeds] + self.get_attachment_embed_list(msg) + evaled_content['anchors'],
                    'anonc_id': anonc_id if self.client.show_chat_id else '????'
                },
            'ext':
                {
                    msg.author.id:
                        {
                            'username': msg.author.nick or self.default_name,
                            'avatar_url': msg.author.avatar_url,
                            'anonc_id': 'YOU'
                        }
                }
        }
        for member_id, content in evaled_content['content'].items():
            body['ext'].setdefault(member_id, {}).update({'content': content})
        from pprint import pprint
        pprint(body)
        return AnoncMessage(body=body, count=count)

    @staticmethod
    def message_to_anchor_dict(message) -> dict:
        print(message.created_at.isoformat())
        return {
            'author': {
                'name': message.author.name,
            },
            'description': message.content,
            'timestamp': message.created_at.isoformat(),
            'footer': {
                'text': 'created at'
            }
        }
        
    @staticmethod
    def get_attachment_embed_list(msg) -> list:
        attachment_embed_list = [{
                'title': 'attachments',
        }]
        image_attachments = []
        not_image_attachments = []
        for a in reversed(msg.attachments):
            base_embed = {
                'title': 'attachments',
            }
            url = a.proxy_url
            if url.split('.')[-1] in ('jpg','jpeg','png','webp','gif'):
                image_attachments.append(url)
            else:
                not_image_attachments.append(url)
        
        if not not_image_attachments and not image_attachments:
            return []
        elif not not_image_attachments:
            image_url = image_attachments.pop()
            attachment_embed_list[0].setdefault('image',{})['url'] = image_url
            
        if not_image_attachments:
            attachment_embed_list[0]['description'] = '•'+'\n•'.join(not_image_attachments)
        for image_url in image_attachments:
            attachment_embed_list.append({'image':{'url':image_url}})
        
        return attachment_embed_list
        
    async def pickup_anonc_mentions(self, content) -> tuple:
        """
        (@({count}|{id}))|(<@&{id_role_id}>)
        """
        mentions = []
        for i in self.mention_pat_role.findall(content):
            anonc_ch = self.client.anonc_guild.get_anonc_chat_channel_from_anonc_id_role_id(int(i))
          
            if anonc_ch:
              mentions.append((f'<@&{i}>',anonc_ch.anonc_id, anonc_ch.anonc_member))
        for i,*f in self.mention_pat_anonc.findall(content):
            exist = False
            if f[0] and int(f[0])<=self.client.anonc_count: # count
                msg = await self.client.get_message_numbered(int(f[0]))
                if not msg:
                    continue
                anonc_id = msg.content.splitlines()[0][3:] # id:hoge → hoge
            else: # id
                anonc_id = f[1]
          
            if not anonc_id:
                continue
                
            anonc_ch = self.client.anonc_guild.get_anonc_chat_channel_from_anonc_id(anonc_id)
            if not anonc_ch:
                continue
            
            mentions.append((f'@{i}',i,anonc_ch.anonc_member))
        
        return mentions

    def pickup_anchors(self, content) -> tuple:
        """
        >>{count}
        """
        return tuple(int(i) for i in self.anchor_pat.findall(content))

    async def eval_content(self, content, count):
        evaluated = {
            'content': {
                'general': content
            },
            'anchors': []
        }

        # anchor
        anchors = self.pickup_anchors(content)
        for num in anchors:
            if num >= count:
                # TODO : future anchor
                ...
            else:
                anchored_message = await self.client.get_message_numbered(num)
                if not anchored_message:
                    # TODO : anchor error handler
                    print(f'error: not found message at {num} ')
                    ...
                    continue

                evaluated['content']['general'] = evaluated['content']['general'].replace(f'>>{num}',
                                                                                          f':msg_anchor:{num}')
                anchor_body = self.message_to_anchor_dict(anchored_message)
                evaluated['anchors'].append(anchor_body)

        # mention
        anonc_mentions = await self.pickup_anonc_mentions(content)
        for i in anonc_mentions:
            evaluated['content']['general'] = evaluated['content']['general'].replace(i[0], ':at_sign:' + i[1])
        for i in anonc_mentions:
            evaluated['content'][i[2].id] = evaluated['content']['general'].replace(':at_sign:' + i[1],
                                                                                        i[2].mention)

        return evaluated

