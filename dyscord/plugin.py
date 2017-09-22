from discord.ext.commands import Command
from dyscord_plugin.plugin import DyscordPlugin
from typing import Dict

from .error import PluginAlreadyImported
from .redis import RedisStorageManager

PLUGIN_CFG_FMT = "plugins.{}.plugin_cfgs.{}"


class ServerPluginHandler:
    def __init__(self, guild_id, redis):
        self.guild_id = guild_id
        self.redis = redis
        self.plugins: Dict[str, DyscordPlugin] = {}

    def add_plugin(self, name, plugin):
        if name in self.plugins:
            raise PluginAlreadyImported
        self.plugins[name] = plugin

    async def process_msg(self, msg):
        if not msg.guild.id == self.guild_id:  # Not part of guild
            return

        for name, p in self.plugins.items():
            await p.process_msg(msg, RedisStorageManager(self.redis, PLUGIN_CFG_FMT.format(self.guild_id, name)))
