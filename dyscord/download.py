import importlib, pkgutil
from urllib import request
import tempfile
import tarfile
import shutil
import json
import os

from typing import List

from dyscord_plugin.plugin import DyscordPlugin

from .error import PluginNotFound, PluginExists, PluginMalformedError

from .plugin_bin import PLUGIN_DIR
PLUGIN_PACKAGE_NAME = os.path.basename(PLUGIN_DIR)
print("Loading plugins from: ", PLUGIN_DIR)

BASE_PACKAGE = "dyscord"

PLUGIN_DB = {"plugin": {"download_link": "https://github.com/dyscord/example-plugin/archive/master.tar.gz"}}  # TODO: PLACEHOLDER
PLUGIN_INFO_FILE = "dyscord-plugin.json"

PLUGIN_CLASS_NAME = "Plugin"


def collect_plugin_info(name):
    try:
        # TODO: Replace with actual package system.
        return PLUGIN_DB[name]
    except KeyError:
        raise PluginNotFound


def module_search(p: str) -> List[pkgutil.ModuleInfo]:
    return list(pkgutil.iter_modules([p]))


class PluginManager:
    def __init__(self):
        self.loaded = {}

    @property
    def downloaded(self):  # Get list of downloaded plugin names
        return [x.name for x in pkgutil.iter_modules([PLUGIN_DIR])]

    def import_plugin(self, name):
        plug = importlib.import_module(".{}.{}".format(PLUGIN_PACKAGE_NAME, name), BASE_PACKAGE)
        Plugin = getattr(plug, PLUGIN_CLASS_NAME)
        try:
            if not issubclass(Plugin, DyscordPlugin):
                raise AttributeError
        except AttributeError:
            raise PluginMalformedError("Does not subclass DyscordPlugin.")
        self.loaded[name] = Plugin
        return Plugin

    @staticmethod
    def download_plugin(name):
        # Create temporary directory for the setup of the plugin:
        td = tempfile.TemporaryDirectory()
        try:
            temp_dir = td.name
            plugin_tar_loc = os.path.join(temp_dir, "plugin.tar.gz")  # Set download location

            # Request plugin info:
            plugin_info = collect_plugin_info(name)

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
