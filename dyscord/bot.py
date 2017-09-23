from redis import StrictRedis
import parse

import discord
from discord.ext.commands import Bot, command, Command
from .plugin import ServerPluginHandler, PLUGIN_LIST_FMT
from .download import PluginManager
from .error import PluginError, PluginAlreadyImported
import os

from typing import Dict

# Bot version
VERSION = 'v0.1'

COMMAND_PREFIX = "d/"


class Dyscord(Bot):
    def __init__(self):
        super().__init__(COMMAND_PREFIX)

        self.server_phandlers: Dict[discord.Guild, ServerPluginHandler] = {}
        self.pm = PluginManager(self)
        self.redis = StrictRedis(charset="utf-8", decode_responses=True)

        # Add all commands in class:
        for m in dir(self):
            attr = getattr(self, m)
            if isinstance(attr, Command):
                self.add_command(attr)

        # Load plugin handlers for existing guilds:
        search = PLUGIN_LIST_FMT.format("*", "*")
        for gname in self.redis.scan_iter(search):  # Search redis for plugin lists
            guild_id = int(parse.parse(PLUGIN_LIST_FMT, gname)[0])  # Extract guild id
            self._get_plugin_handler(guild_id)  # Create all plugin handlers of existing guilds

    def _get_plugin_handler(self, guild_id):
        if guild_id in self.server_phandlers:  # If the guild handler has been created
            ph = self.server_phandlers[guild_id]  # Get from list
        else:  # Guild is new
            ph = ServerPluginHandler(guild_id, self.redis, self.pm)  # Create plugin handler
            self.server_phandlers[guild_id] = ph  # Add handler to list
        return ph

    @command(pass_context=True)
    async def plugin_install(self, ctx, plugin_name: str):
        _guild = ctx.guild
        _channel = ctx.channel

        ph = self._get_plugin_handler(_guild.id)  # Get plugin handler from guild id

        try:
            try:
                ph.add_plugin(plugin_name)
            except PluginAlreadyImported:
                await _channel.send("Already implemented plugin: {}".format(plugin_name))
            else:
                await _channel.send("Successfully implemented plugin: {}".format(plugin_name))
        except PluginError as e:
            await _channel.send("Error implementing plugin: {}".format(e.__class__.__name__))

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        if message.author == self.user:  # Ignore if message is from this bot
            return

        await super().on_message(message)  # Run local commands
        for ph in self.server_phandlers.values():
            await ph.process_msg(message)

    async def on_command_error(self, *args, **kwargs):  # Prevent reporting of missing commands (could be in plugin)
        pass
