import os
from dyscord import Bot
from dyscord.download import delete_all_plugins

delete_all_plugins()  # Delete all cached plugins

b = Bot()

b.run(os.environ["DYSCORD_TOKEN"])
