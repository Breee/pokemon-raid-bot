import logging

log_path = '.'
log_file = 'raidquaza'

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
LOGGER = logging.getLogger('discord')

fileHandler = logging.FileHandler("{0}/{1}.log".format(log_path, log_file))
fileHandler.setFormatter(logFormatter)
LOGGER.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
LOGGER.addHandler(consoleHandler)
LOGGER.setLevel(level=logging.INFO)

from pollbot.PollBot import PollBot

if __name__ == "__main__":
    LOGGER.info("Starting Bot.")
    bot = PollBot(prefix="!raid-", description="", config_file="config.conf")
    bot.run()
