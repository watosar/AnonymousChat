import re
from datetime import timezone, timedelta

timezone = timezone(timedelta(hours=9))


def jst(timestamp):
    return timestamp.astimezone(timezone)


class AnoncMessage:
    def __init__(self, body, count):
        self.body = body
        self.count = count

    def to_dict(self, anonc_channel):
        adapted = self.body['general']
        ext = self.body['ext'].get(anonc_channel.member.id, {})
        for k, v in ext.items():
            adapted.setdefault(k, v)
        adapted['username'] = f'{self.count}:{adapted["username"]}'
        return adapted


class AnoncMessageMaker:
    def __init__(self, client):
        self.client = client
        self.anchor_pat = re.compile('(?=(?<=^)|(?<= ))>>([0-9]+)(?= |$)')
        self.mention_pat_role = re.compile('<@&([0-9]+)>')
        self.mention_pat_anonc = re.compile('@(([0-9]+)|([A-Za-z]{3,}))')

    @staticmethod
    def message_to_anchor_dict(message) -> dict:
        return {
            'author': {
                'name': message.author.name,
            },
            'description': message.content,
            'timestamp': str(jst(message.created_at).data())
        }

    async def pickup_anonc_mentions(self, content) -> tuple:
        """
        (@({count}|{id}))|(<@&{id_role_id}>)
        """
        mentions = []
        for i in self.mention_pat_role.findall(content):
          anonc_id_role = self.client.anonc_guild.get_role(int(i))
          if anonc_id_role:
            mentions.append((f'<@&{i}>',anonc_id_role.name, anonc_id_role.member))
        for i,*f in self.mention_pat_count.findall(content):
          exist = False
          if f[0] and int(f[0])<=self.client.count: # count
            anonc_id = await self.client.get_message_numbered(int(f[0])).splitlines()[0][3:]
          else: # id
            anonc_id = f[1]
          
          if anonc_id:
            anonc_id_role = self.client.anonc_guild.get_role_named(anonc_id)
            if anonc_id_role:
              mentions.append((f'@{i}',i,anonc_id_role.member))
        
        return mentions

    def pickup_anchors(self, content) -> tuple:
        """
        >>{count}
        """
        return tuple(self.anchor_pat.findall(content))

    async def eval_content(self, content, count):
        evaluated = {
            'content': {
                'general': content
            },
            'anchors': []
        }

        # anchor
        anchor_emoji = self.client.anonc_guild.get_emoji_named['anchor']  # <:anchor:00000>
        anchors = self.pickup_anchors(content)
        for num in anchors:
            if num > count:
                # TODO : future anchor
                ...
            else:
                anchored_message = await self.client.get_numbered_message(num)
                if not anchored_message:
                    # TODO : anchor error handler
                    print(f'error: not found message at {num} ')
                    ...
                    continue

                evaluated['content']['general'] = evaluated['content']['general'].replace(f'>>{num}',
                                                                                          f'{anchor_emoji}{num}')
                anchor_body = self.message_to_anchor_dict(anchored_message)
                evaluated['anchors'].append(anchor_body)

        # mention
        mention_emoji = self.client.anonc_guild.get_emoji_named['at_sign']  # <:at_sign:0000000>
        anonc_mentions = await self.pickup_anonc_mentions(content)
        for i in anonc_mentions:
            evaluated['content']['general'] = evaluated['content']['general'].replace(i[0], mention_emoji + i[1])
        for i in anonc_mentions:
            evaluated['content'][i[2].id] = evaluated['content']['general'].replace(mention_emoji + i[1],
                                                                                        i[2].mention)

        return evaluated

    async def make(self, msg, count) -> AnoncMessage:
        anonc_id = self.client.anonc_guild.get_id_from_channel(msg.channel)
        msg.content = f'ID:{anonc_id}\n'
        evaled_content = await self.eval_content(msg.content, count)
        body = {
            'general':
                {
                    'username': 'jhon doe',
                    'content': evaled_content['content'].pop('general'),
                    'embeds': [i.to_dict() for i in msg.embeds] + evaled_content['anchors']
                },
            'ext':
                {
                    msg.author.id:
                        {
                            'username': msg.author.nick,
                            'avatar_url': msg.author.avatar_url
                        }
                }
        }
        for member_id, content in evaled_content['content'].items():
            body['ext'].setdefault(member_id, {}).update({'content': content})
        return AnoncMessage(body=body, count=count)
