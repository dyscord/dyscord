from redis import StrictRedis

import discord
from discord.ext.commands import Bot, command, Command
from .plugin import ServerPluginHandler
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

    @command(pass_context=True)
    async def plugin_install(self, ctx, plugin_name: str):
        _guild = ctx.guild
        _channel = ctx.channel

        if _guild in self.server_phandlers:  # If the guild handler has been created
            ph = self.server_phandlers[_guild]
        else:  # Guild is new
            ph = ServerPluginHandler(_guild.id, self.redis)  # Create plugin handler
            self.server_phandlers[_guild] = ph

        try:
            try:
                ph.add_plugin(plugin_name, self.pm.get_plugin(plugin_name))
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
