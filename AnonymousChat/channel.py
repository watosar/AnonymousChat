import discord

class AnoncChannel:
  __slots__=('core','anonc_member','anonc_webhook')
  
  def __init__(self,core, anonc_webhook, anonc_member=None, anonc_role = None):
    self.core = core
    self.anonc_webhook = anonc_webhook
    member_id, role_id = anonc_webhook.name.split(':')
    self.anonc_member = anonc_member or channel.guild.get_member(int(member_id,36))
    self.anonc_role = anonc_role or channel.guild.get_role(int(role_id, 36))
    
    
  def __getattr__(self, key):
    if key not in self.__slots__:
      return getattr(self.core,key)
    else:
      return getattr(self,key)
  
  def __eq__(self, other):
    return self.core == other
    
  def is_equal_to(self, channel):
    return self == channel
