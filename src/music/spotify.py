# TODO: Integration with Spotify Web API pending client credentials

import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .interface import IMusicProvider

from shared.logger import get_logger
from shared.decorator import retry_on_failure
from shared.config import settings


class SpotifyMusicService(IMusicProvider):

    _instance = None

    def __init__(self):
        self._logger = get_logger("SPOTIFY")
        self._sp = None
        self._active_device_id = None

    def __new__(cls):
        if cls._instance:
            return cls._instance
        
        cls._instance =  super(SpotifyMusicService, cls).__new__(cls)
        return cls._instance

    def connect(self) -> None:

        try:

            auth_manager = SpotifyOAuth(
                client_id=settings.SPOTIFY_ID,
                client_secret=settings.SPOTIFY_SECRET,
                scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
                cache_path=".spotify_cache", 
                open_browser=False
            )

            self._sp = spotipy.Spotify(auth_manager=auth_manager)

            self._refresh_active_device()
            self.log.info("🟢 Spotify Service Connected.")

        except Exception as e:

            self.log.critical(f"🔴 Errore critico inizializzazione Spotify: {e}")
            raise

    def _refresh_active_device(self) -> None:

        """
        Search for an active device to play music
        """

        try:

            devices = self._sp.devices()

            active = [d for d in devices['devices'] if d['is_active']]

            if active:

                self._active_device_id = active[0]['id']

            elif devices['devices']: # no active device

                self.active_device_id = devices['devices'][0]['id']
                self.log.warning(f"🟡 No active device. Selected fallback: {devices['devices'][0]['name']}")

            else:

                self.active_device_id = None
                self.log.error("🔴 No device found for spotify! Open Spotify on PC/Mobile.")

        except Exception as e:
            
            self.log.error("🔴 Error during device search: {e}")
            raise


    @retry_on_failure(max_retries=3, base_delay=1.0)
    def play_genre(self, genre) -> None:
        pass

    
    def set_volume(self, level) -> None:
        if self._sp and self._active_device_id:
            
            try:
                
                self.sp.volume(level, device_id=self.active_device_id)
                self._logger.debug(f"🟢 Increased volume to level {level} on active device {self._active_device_id}")

            except Exception as e:

                self.log.error(f"🔴 Error rising volume to level {level} on active device {self._active_device_id}: {e}")


    def stop(self) -> None:
        if self._sp and self._active_device_id:

            try:
            
                self._sp.pause_playback(device_id=self._active_device_id)
                self._logger.debug(f"🟢 Stopped music on active device {self._active_device_id}")
            
            except Exception as e:

                self.log.error(f"🔴 Error while stopping music on active device {self._active_device_id}: {e}")
        