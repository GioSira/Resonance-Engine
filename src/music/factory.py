from .interface import IMusicProvider
from .spotify import SpotifyMusicService

from enum import Enum


class ProviderEnum(str, Enum):

    SPOTIFY = 'SPOTIFY'


class MusicFactory(object):

    @staticmethod
    def get_music_provider(provider_type: ProviderEnum) -> IMusicProvider:

        if provider_type == ProviderEnum.SPOTIFY:
            
            instance = SpotifyMusicService()

        else:
            raise ValueError(f"Music provider {provider_type} not supported. Valid values are [spotify]")

        instance.connect()

        return instance
