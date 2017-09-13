# Plugin:
class PluginNotFound(ValueError):
    """ Throw if plugin requested for download does not exist """
    pass


class PluginExists(FileExistsError):
    """ Throw if plugin requested for download already exists """


class PluginMalformedError(ValueError):
    """ Throw if downloaded plugin is malformed """
    pass
