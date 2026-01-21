from .redis import RedisCache
from .interface import ICache
from enum import Enum

class CacheEnum(str, Enum):

    REDIS = "REDIS"


class CacheFactory(object):

    @staticmethod
    def get_cache(cache_type: CacheEnum) -> ICache:

        if cache_type == CacheEnum.REDIS:
            instance =  RedisCache()
        else:
            raise ValueError(f"Cache type '{cache_type}' not supported. Valid values are [REDIS]")
        
        instance.connect()

        return instance
