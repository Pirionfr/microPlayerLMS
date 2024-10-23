import logging
import os

LMS_SERVER = os.getenv("LMS_SERVER", "127.0.0.1")
PLAYER_NAME = os.getenv("PLAYER_NAME", "default")

SPOTIFY_USER = os.getenv("SPOTIFY_USER", "default")

PARTIAL_UPDATE_COUNT = int(os.getenv("PARTIAL_UPDATE_COUNT", 100))
FULL_REFRESH_TIME = int(os.getenv("FULL_REFRESH_TIME", 12))

LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
