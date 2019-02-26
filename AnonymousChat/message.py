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
        self.mention_pat = re.compile('<@(&[0-9]+)>|@([0-9]+|[A-Za-z]{3,})')

    @staticmethod
    def message_to_anchor_dict(message) -> dict:
        return {
            'author': {
                'name': message.author.name,
            },
            'description': message.content,
            'timestamp': str(jst(message.created_at).data())
        }

    def pickup_anonc_mentions(self, content) -> tuple:
        """
        (@({count}|{id}))|(<@?{id_role_id}>)
        """

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
                    ...
                    continue

                evaluated['content']['general'] = evaluated['content']['general'].replace(f'>>{num}',
                                                                                          f'{anchor_emoji}{num}')
                anchor_body = self.message_to_anchor_dict(anchored_message)
                evaluated['anchors'].append(anchor_body)

        # mention
        mention_emoji = self.client.anonc_guild.get_emoji_named['at_sign']  # <:at_sign:0000000>
        anonc_mentions = self.pickup_anonc_mentions(content)
        for i in anonc_mentions:
            evaluated['content']['general'] = evaluated['content']['general'].replace(i, mention_emoji + i.name)
        for i in anonc_mentions:
            evaluated['content'][i.menber.id] = evaluated['content']['general'].replace(mention_emoji + i.name,
                                                                                        i.member.mention)

        return evaluated

    async def make(self, msg, count) -> AnoncMessage:
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

