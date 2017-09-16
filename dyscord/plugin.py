from discord.ext.commands import Command
from dyscord_plugin.plugin import DyscordPlugin
from typing import Dict

from .error import PluginAlreadyImported


class ServerPluginHandler:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.plugins: Dict[str, DyscordPlugin] = {}

    def add_plugin(self, name, plugin):
        if name in self.plugins:
            raise PluginAlreadyImported
        self.plugins[name] = plugin

    async def process_msg(self, msg):
        if not msg.guild.id == self.guild_id:  # Not part of guild
            return

        for p_i in self.plugins.items():
            p = p_i[1]
            await p.process_msg(msg)
