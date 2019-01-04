import re
from discord import Embed
ancher_pattern = re.compile('>>\d+')

class AnoncMessage():
  
  def __init__(self,message):
    self._content = message.content
    self.author = message.author
    self.channel = message.channel
    self.anchered_messages = []
    
  @property
  def anchers(self):
  	return [int(ancher[2:]) for ancher in ancher_pattern.findall(self.plane_content)]
  
  def embeds_from_anchered_messages(self):
  	embeds = []
  	for anchered_message in self.anchered_messages:
  		embed = Embed(
  			description = anchered_message.content
  		)
  		embed.set_author(anchered_message.author.name)
  
  def addupt_for_channel(self, anonc_channel):
  	if anonc_channel.is_equal_to(self.channel):
  	  self._content = self._content.replace(anonc_channel.anonc_role.mention,anonc_channel.anonc_member.mention)
  	  self.icon_url = anonc_channel.anonc_member.icon_url
  	  
  def to_dict(self):
    
    return {content='',username='{count}:名無し',icon_url=self.icon_url,embeds=self.anchered_message_embeds}
