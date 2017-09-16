# Plugin:
class PluginError(Exception):
    """ General plugin error """
    pass


class PluginNotFound(PluginError):
    """ Throw if plugin requested for download does not exist """
    pass


class PluginExists(PluginError):
    """ Throw if plugin requested for download already exists """


class PluginMalformedError(PluginError):
    """ Throw if downloaded plugin is malformed """
    pass


# Plugin Implementation
class PluginAlreadyImported(ValueError):
    """ Throw if a plugin has already been downloaded """
    pass
