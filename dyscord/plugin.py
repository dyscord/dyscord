from discord.ext.commands import Command
from dyscord_plugin.plugin import DyscordPlugin
from typing import Dict

from .error import PluginAlreadyImported
from .redis import RedisStorageManager
from .download import PluginManager

PLUGIN_LIST_BASE = "plugins.{}.plugin_list"
PLUGIN_LIST_FMT = PLUGIN_LIST_BASE + ".{}"
PLUGIN_CFG_FMT = "plugins.{}.plugin_cfgs.{}"


class ServerPluginHandler:
    def __init__(self, guild_id, redis, pm: PluginManager):
        self.guild_id = guild_id
        self.redis = redis
        self.plugin_list = RedisStorageManager(self.redis, PLUGIN_LIST_BASE.format(self.guild_id))
        self.pm = pm

    def add_plugin(self, name):
        if name in self.plugin_list:
            raise PluginAlreadyImported
        self.plugin_list[name] = True  # Add key

    async def process_msg(self, msg):
        if not msg.guild.id == self.guild_id:  # Not part of guild
            return

        for name in self.plugin_list:
            p = self.pm.get_plugin(name)
            await p.process_msg(msg, RedisStorageManager(self.redis, PLUGIN_CFG_FMT.format(self.guild_id, name)))
