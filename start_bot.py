import logging

log_path = '.'
log_file = 'raidquaza'

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger('raidquaza')

fileHandler = logging.FileHandler("{0}/{1}.log".format(log_path, log_file))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(level=logging.INFO)

from pollbot.PollBot import PollBot

if __name__ == "__main__":
    rootLogger.info("Starting Bot.")
    bot = PollBot(prefix="!raid-", description="", config_file="config.conf")
    bot.run()
