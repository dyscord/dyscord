import os
from dyscord import Bot

b = Bot()

b.run(os.environ["DYSCORD_TOKEN"])
