import asyncio
import io
import logging
import urllib.parse

import aiohttp
from PIL import Image
from pysqueezebox import Server
from . import get_asset_path


class Track:
    def __init__(self, title="", artist="", album="", duration=None, artwork=None, time=0):
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.artwork = artwork
        self.time = time


class Album:
    def __init__(self, artist="", album="", artwork=None, url=""):
        self.artist = artist
        self.album = album
        self.artwork = artwork
        self.url = url


class Player:
    MAX_RETRIES = 3  # Number of retries for network requests
    TIMEOUT = 5

    def __init__(self, server, player_name, user):
        self.stop_subscribing = asyncio.Event()
        self.LMS = server
        self.player_name = player_name
        self.user = user
        self.player_status = "pause"

        self.subscribe_task = asyncio.create_task(self.subscribe_to_player_events())
        self.current_track = None

    async def _get_player(self, session):
        """Helper method to fetch the player object."""
        lms = Server(session, self.LMS)
        player = await lms.async_get_player(name=self.player_name)
        if player is None:
            raise ValueError(f"player {self.player_name} not found")
        return player

    async def _get_image(self, session, url):
        """Helper method to fetch and return an image with retries.
        If fetching fails, it loads a local fallback image.
        """
        logging.debug(f"Trying to get image from URL: {url}")
        for attempt in range(self.MAX_RETRIES):
            try:
                async with session.get(url=url) as response:
                    response.raise_for_status()  # Raise an error for bad responses
                    buffer = io.BytesIO(await response.read())
                    return Image.open(buffer)
            except aiohttp.ClientError as e:
                logging.warning(f"Attempt {attempt + 1} - Error fetching image: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    logging.error("All attempts to fetch image failed, loading fallback image.")
                    break  # Exit the retry loop to load the fallback image
            except asyncio.TimeoutError:
                logging.warning(f"Attempt {attempt + 1} - Timeout while fetching image.")
                if attempt == self.MAX_RETRIES - 1:
                    logging.error("All attempts to fetch image timed out, loading fallback image.")
                    break  # Exit the retry loop to load the fallback image

        # Load local fallback image
        return Image.open(get_asset_path('fallback.png'))

    async def _get_spotify_item_id(self, player):
        """Helper method to get the Spotify user ID."""
        results = await player.async_query("spotty", "items", "0", "255", "menu:spotty")
        for result in results["item_loop"]:
            if result["text"] == self.user:
                return result["actions"]["go"]["params"]["item_id"]
        return ""

    def _generate_image_url(self, url):
        """Helper method to generate image URL using the LMS."""
        lms = Server(None, self.LMS)
        return lms.generate_image_url(url)

    async def get_spotify_favorite(self):
        sync_album_task = asyncio.create_task(self.get_spotify_albums())
        sync_playlists_task = asyncio.create_task(self.get_spotify_playlists())

        playlists = await sync_playlists_task
        albums = await sync_album_task

        playlists.extend(albums)
        return playlists

    async def get_spotify_playlists(self):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            item_id = await self._get_spotify_item_id(player)

            if not item_id:
                return []

            playlists = []
            results = await player.async_query("spotty", "items", "0", "255", "menu:spotty", f"item_id:{item_id}.3")
            for item in results["item_loop"]:
                img = await self._get_image(session, item["presetParams"]["icon"])
                playlists.append(
                    Album(album=item["text"], artist=self.user, artwork=img, url=item["presetParams"]["favorites_url"])
                )
            return playlists

    async def get_spotify_albums(self):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            item_id = await self._get_spotify_item_id(player)
            if not item_id:
                return []

            results = await player.async_query(
                "spotty", "items", "0", "255", "menu:spotty", f"item_id:{item_id}.1"
            )

            albums = []
            for item in results["item_loop"]:
                img = await self._get_image(session, item["presetParams"]["icon"])
                txt = item["text"].split("\n")
                albums.append(
                    Album(album=txt[0], artist=txt[1], artwork=img, url=item["presetParams"]["favorites_url"])
                )
            return albums

    async def pause(self):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            await player.async_pause()

    async def play_url(self, url):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            await player.async_load_url(url)

    async def play(self):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            asyncio.run(player.async_play())

    async def next(self):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            await player.async_query("playlist", "index", "+1")

    async def previous(self):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            await player.async_query("button", "jump_rew")

    async def update_current_track(self):
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)
            await player.async_update()

            if not player.current_track:
                return None

            img_url = self._generate_image_url(player.current_track["artwork_url"])  # Generate the image URL

            artist = ""
            if "artist" in player.current_track:
                artist = player.current_track["artist"]

            album = ""
            if "album" in player.current_track:
                album = player.current_track["album"]

            self.current_track = Track(
                title=player.current_track["title"],
                artist=artist,
                album=album,
                duration=player.duration_float,
                artwork=await self._get_image(session, img_url),
                time=player.time
            )

    async def subscribe_to_player_events(self):
        """Subscribe to player events for the given player_id."""
        async with aiohttp.ClientSession() as session:
            player = await self._get_player(session)

            reader, writer = await asyncio.open_connection(self.LMS, 9090)
            writer.write(f"{player.player_id} subscribe pause,stop,play,playlist newsong\n".encode())
            await writer.drain()

            logging.debug(f"Subscribed to player {player.player_id} events.")

            # Continuously read event messages
            while not self.stop_subscribing.is_set():
                response = await reader.readline()
                event = urllib.parse.unquote(response.decode().strip())
                await self.handle_event(event)

        if writer:
            writer.close()
            await writer.wait_closed()
            logging.debug("Connection closed")

    async def handle_event(self, event_response):
        """Handle LMS player events by parsing the event response."""
        logging.debug(f"Received event: {event_response}")

        # Split the event response into parts
        parts = event_response.split()

        if len(parts) < 2:
            logging.debug("Unknown event format")
            return

        player_id = parts[0]  # Player ID
        command = parts[1]  # Event command (like playlist, play, pause)

        # Handle different event types
        if command == 'playlist':
            if 'newsong' in parts:
                await self.update_current_track()
            if 'stop' in parts:
                logging.debug(f"Player {player_id} paused.")
                self.player_status = 'pause'

        elif command == 'play':
            # Handle play event
            logging.debug(f"Player {player_id} started playing.")
            self.player_status = 'play'

        elif command == 'pause':
            # Handle pause event
            if '1' in parts:
                logging.debug(f"Player {player_id} paused.")
                self.player_status = 'pause'
            else:
                logging.debug(f"Player {player_id} resumed playing.")
                # Add logic here for resuming from pause
                self.player_status = 'play'
