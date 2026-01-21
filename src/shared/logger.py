import logging
import os
import sys
from logging.handlers import RotatingFileHandler

class _Logger(object):

    _logger = None
    _folder = None

    def __init__(self, folder):
        
        self._folder = folder
        
        if not os.path.exists(self._folder):
            os.makedirs(self._folder)

    @classmethod
    def get_logger(cls, name: str = "CORE"):
        
        # if logger already exists
        if cls._logger:
            return cls._logger.getChild(name)
        
        # Base configuration
        logger = logging.getLogger("ROOT")
        logger.setLevel(logging.DEBUG)

        # format output
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # handle console stream
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # handle file rotation
        file_handler = RotatingFileHandler(
            filename=os.path.join(cls._folder, "core.log"),
            maxBytes=5*1024*1024, # 5MB
            encoding='utf-8',
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        # avoid logger propagation for multiple calls
        logger.propagate = False

        return logger.getChild(name)
    

def get_logger(module_name):
    return _Logger.get_logger(module_name)
