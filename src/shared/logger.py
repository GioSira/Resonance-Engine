import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from src.shared.config import settings

class _Logger(object):

    _logger = None
    _folder = settings.LOG_FOLDER

    
    @classmethod
    def _initialize_folder(cls):
        
        if not os.path.exists(cls._folder):
            os.makedirs(cls._folder, exist_ok=True)
        

    @classmethod
    def get_logger(cls, name: str = "CORE"):
        
        # if logger already exists
        if cls._logger:
            return cls._logger.getChild(name)
        
        cls._initialize_folder()
        
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
