import importlib, pkgutil
from urllib import request
import tempfile
import tarfile
import shutil
import json
import os

from typing import List

from discord.ext.commands import Bot

from dyscord_plugin.plugin import DyscordPlugin

from .error import PluginNotFound, PluginExists, PluginMalformedError

from .plugin_bin import PLUGIN_DIR
PLUGIN_PACKAGE_NAME = os.path.basename(PLUGIN_DIR)
print("Loading plugins from: ", PLUGIN_DIR)

BASE_PACKAGE = "dyscord"

DYPI_URL = "https://github.com/dyscord/pi/archive/master.tar.gz"
DYPI_FOLDER = "pi-master/dypi"
DYPI_ENTRY_EXT = ".json"

PLUGIN_INFO_FILE = "dyscord-plugin.json"

PLUGIN_CLASS_NAME = "Plugin"


def collect_plugin_list():
    with tempfile.TemporaryDirectory() as td:
        download_file = os.path.join(td, "dypi.tar.gz")
        request.urlretrieve(DYPI_URL, download_file)

        # Open downloaded tarfile:
        plugin_tarfile = tarfile.open(download_file, mode='r:gz')

        # Extract:
        extract_dir = os.path.join(td, "extract")  # Set extraction location
        plugin_tarfile.extractall(path=extract_dir)  # EXTRACT!!!

        dypi_dir = os.path.join(extract_dir, DYPI_FOLDER)
        pkgs = {}

        for p in os.listdir(dypi_dir):
            with open(os.path.join(dypi_dir, p), mode='r') as f:
                p_info = json.load(f)

            pkgs[p[:-len(DYPI_ENTRY_EXT)]] = {"download_link": p_info["download_link"]}

    return pkgs


def module_search(p: str) -> List[pkgutil.ModuleInfo]:
    return list(pkgutil.iter_modules([p]))


class PluginManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.loaded = {}
        self.plugin_list = collect_plugin_list()

    @property
    def downloaded(self):  # Get list of downloaded plugin names
        return [x.name for x in pkgutil.iter_modules([PLUGIN_DIR])]

    def import_plugin(self, name):
        plug = importlib.import_module(".{}.{}".format(PLUGIN_PACKAGE_NAME, name), BASE_PACKAGE)
        plugin = getattr(plug, PLUGIN_CLASS_NAME)(self.bot)
        try:
            if not isinstance(plugin, DyscordPlugin):
                raise AttributeError
        except AttributeError:
            raise PluginMalformedError("Does not subclass DyscordPlugin.")
        self.loaded[name] = plugin
        return plugin

    def get_plugin_info(self, name):
        try:
            return self.plugin_list[name]
        except KeyError:
            raise PluginNotFound

    def download_plugin(self, name):
        # Create temporary directory for the setup of the plugin:
        td = tempfile.TemporaryDirectory()
        try:
            temp_dir = td.name
            plugin_tar_loc = os.path.join(temp_dir, "plugin.tar.gz")  # Set download location

            # Request plugin info:
            plugin_info = self.get_plugin_info(name)

            # Download plugin to temporary location:
            request.urlretrieve(plugin_info["download_link"], plugin_tar_loc)

            # Open downloaded tarfile:
            plugin_tarfile = tarfile.open(plugin_tar_loc, mode='r:gz')
            plugin_dir_name = plugin_tarfile.getnames()[0]  # Get dir name from first member - POTENTIALLY A FUTURE ISSUE
            # TODO: FIX THIS DIRECTORY NAME COLLECTION

            # Extract:
            extract_dir = os.path.join(temp_dir, "plugin")  # Set extraction location
            plugin_tarfile.extractall(path=extract_dir)  # EXTRACT!!!

            try:
                # Get plugin directory
                plugin_dir = os.path.join(extract_dir, plugin_dir_name)
                # Open plugin info from extraction
                with open(os.path.join(plugin_dir, PLUGIN_INFO_FILE), mode='r') as pf:
                    plugin_info = json.load(pf)

                # Get package name:
                package_name = plugin_info["package"]
                version = plugin_info["version"]
            except FileNotFoundError:  # Catch if info file is missing
                raise PluginMalformedError
            else:
                print("Downloading {} ({})".format(name, version))

            try:
                # Copy tmp plugin package to plugin directory:
                shutil.copytree(os.path.join(plugin_dir, package_name), os.path.join(PLUGIN_DIR, name))
            except FileExistsError:
                raise PluginExists
        finally:
            # Close temporary directory:
            td.cleanup()

    def get_plugin(self, name: str):
        # Return plugin if already loaded
        if name in self.loaded:
            return self.loaded[name]

        if name not in self.downloaded:
            try:
                self.download_plugin(name)
            except PluginExists:  # plugin name was different from actual package
                pass

        return self.import_plugin(name)
