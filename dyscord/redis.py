from redis import StrictRedis
from dyscord_plugin.storage import StorageManager


class RedisStorageManager(StorageManager):
    def __init__(self, redis: StrictRedis, prefix):
        self.redis = redis
        self.prefix = prefix

    def _add_prefix(self, text, add_dot=True):
        if add_dot:
            sep = "."
        else:
            sep = ""

        return "{}{}{}".format(self.prefix, sep, text)

    def __len__(self):
        return sum(1 for x in self.__iter__())

    def __getitem__(self, key):
        return self.redis.get(self._add_prefix(key))

    def __setitem__(self, key, value):
        self.redis.set(self._add_prefix(key), value)

    def __delitem__(self, key):
        self.redis.delete(self._add_prefix(key))

    def __iter__(self):
        for k in self.redis.scan_iter(self._add_prefix("*", add_dot=False)):
            yield k[len(self._add_prefix("")):]

    def __contains__(self, item):
        return self._add_prefix(item) in self.redis

    def get(self, key):
        return self.__getitem__(key)

    def set(self, key, value):
        self.__setitem__(key, value)
