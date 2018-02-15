import logging
import time
logger = logging.getLogger('discord')

class Configuration(object):

    def __init__(self, config_file):
        self.token = ""
        self.playing = ""
        self.msg_update_interval = 100
        self.msg_timeout = 0
        self.read_config_file(config_file)

    def read_config_file(self, config_file):
        """
        >>> Conf = Configuration("test.conf")
        >>> Conf.token
        'TESTTOKEN'
        >>> Conf.playing
        'TESTPLAYING'
        >>> Conf.msg_update_interval
        100
        >>> Conf.msg_timeout
        3600

        :param config_file:
        :return:
        """
        with open(config_file, 'r') as config:
            for line in config:
                if line.startswith("token="):
                    self.token = line[line.find("=") + 1:].rstrip("\n")
                if line.startswith("playing="):
                    self.playing = line[line.find("=") + 1:].rstrip("\n")
                if line.startswith("message_update_interval="):
                    self.msg_update_interval = int(line[line.find("=") + 1:].rstrip("\n"))
                if line.startswith("message_timeout="):
                    self.msg_timeout = int(line[line.find("=") + 1:].rstrip("\n"))
