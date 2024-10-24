import asyncio
import logging
import traceback

from . import config
from .lms import Player
from .display import EinkDisplay


async def main():
    eink_display = None
    try:

        lms_player = Player(config.LMS_SERVER, config.PLAYER_NAME, config.SPOTIFY_USER)
        sync_album_task = asyncio.create_task(lms_player.get_spotify_favorite())
        spotify_albums_index = 0

        eink_display = EinkDisplay(config.FULL_REFRESH_TIME, config.PARTIAL_UPDATE_COUNT)
        current_track = lms_player.current_track
        spotify_albums = await sync_album_task
        while True:
            try:

                eink_display.refresh_if_needed()

                # update current track if on player screen
                if eink_display.is_on_player_screen():
                    if lms_player.current_track is not None:
                        if current_track is None or current_track.title != lms_player.current_track.title:
                            logging.debug("update track information...")
                            current_track = lms_player.current_track
                            eink_display.update_current_track(
                                current_track.title,
                                current_track.album,
                                current_track.artist,
                                current_track.artwork
                            )

                    if lms_player.player_status == "play":
                        eink_display.show_play_pause(False)
                    else:
                        eink_display.show_play_pause(True)

                # Reading touch events and managing interactions.
                touch_event = eink_display.read_touch()
                if touch_event:
                    if touch_event == 'selector':
                        logging.debug("selector icon touched...")
                        eink_display.show_selector()
                        eink_display.show_album(
                            spotify_albums[spotify_albums_index].album,
                            spotify_albums[spotify_albums_index].artist,
                            spotify_albums[spotify_albums_index].artwork,
                        )

                    elif touch_event == 'player':
                        logging.debug("Player icon touched...")
                        eink_display.show_player()
                        await lms_player.update_current_track()
                        eink_display.update_current_track(lms_player.current_track.title,
                                                          lms_player.current_track.album,
                                                          lms_player.current_track.artist,
                                                          lms_player.current_track.artwork)
                        await lms_player.play()

                    elif touch_event == 'launch_player':
                        logging.debug("player icon from menu touched...")
                        eink_display.show_player()
                        await lms_player.play_url(spotify_albums[spotify_albums_index].url)
                        await lms_player.update_current_track()
                        eink_display.update_current_track(lms_player.current_track.title,
                                                          lms_player.current_track.album,
                                                          lms_player.current_track.artist,
                                                          lms_player.current_track.artwork)

                    elif touch_event == 'previous_album':
                        if spotify_albums_index > 0:
                            logging.debug("previous album...")
                            spotify_albums_index -= 1
                            eink_display.show_album(
                                spotify_albums[spotify_albums_index].album,
                                spotify_albums[spotify_albums_index].artist,
                                spotify_albums[spotify_albums_index].artwork,
                            )

                    elif touch_event == 'next_album':
                        if spotify_albums_index < len(spotify_albums) - 1:
                            logging.debug("next album...")
                            spotify_albums_index += 1
                            eink_display.show_album(
                                spotify_albums[spotify_albums_index].album,
                                spotify_albums[spotify_albums_index].artist,
                                spotify_albums[spotify_albums_index].artwork,
                            )

                    elif touch_event == 'return_menu':
                        if spotify_albums_index < len(spotify_albums) - 1:
                            logging.debug("return menu...")
                            eink_display.show_menu()

                    elif touch_event == 'next_track':
                        logging.debug("next track touched...")
                        await lms_player.next()
                        await lms_player.update_current_track()
                        eink_display.update_current_track(
                            lms_player.current_track.title,
                            lms_player.current_track.album,
                            lms_player.current_track.artist,
                            lms_player.current_track.artwork)

                    elif touch_event == 'previous_track':
                        logging.debug("next track touched...")
                        await lms_player.previous()
                        await lms_player.update_current_track()
                        eink_display.update_current_track(
                            lms_player.current_track.title,
                            lms_player.current_track.album,
                            lms_player.current_track.artist,
                            lms_player.current_track.artwork)

                    elif touch_event == 'play_pause':

                        if lms_player.player_status == "play":
                            logging.debug("pause...")
                            await lms_player.pause()
                            eink_display.show_play_pause(True)
                        else:
                            logging.debug("play...")
                            await lms_player.play()
                            eink_display.show_play_pause(False)

                await asyncio.sleep(0.02)

            except Exception as e:
                logging.error(f"Error during screen or music management : {e}")
                logging.debug(traceback.format_exc())

    except IOError as ioe:
        logging.error(f" I/O error : {ioe}")
        logging.debug(traceback.format_exc())
    except Exception as ge:
        logging.error(f"Unexpected error : {ge}")
        logging.debug(traceback.format_exc())
    finally:
        logging.debug("cleaning...")
        if eink_display:
            eink_display.cleanup()
            await eink_display.stop()
