#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import asyncio
from datetime import timedelta, datetime

from PIL import Image, ImageDraw, ImageFont
from lib import epd2in13_V4  # eInk display stuff

from lib import gt1151  # eInk touch stuff
from . import get_asset_path


class EinkDisplay:
    def __init__(self, full_refresh_time, partial_update_count):
        # Initialisation screen
        self.partial_update_count = partial_update_count
        self.full_refresh_delta = timedelta(hours=full_refresh_time)
        self.epd = epd2in13_V4.EPD()
        self.font = ImageFont.truetype(get_asset_path('Font.ttc'), 18)
        self.player = Image.open(get_asset_path('player.bmp'))
        self.menu = Image.open(get_asset_path('menu.bmp'))
        self.selector = Image.open(get_asset_path('selector.bmp'))
        self.canvas = Image.new('1', (self.epd.height, self.epd.width), 255)
        self.baseImage = self.menu
        self.canvas.paste(self.baseImage)

        # Initialisation du tactile
        self.gt = gt1151.GT1151()
        self.GT_Dev = gt1151.GT_Development()
        self.GT_Old = gt1151.GT_Development()
        self.gt.GT_Init()

        # Async task for touch check
        self.stop_touch_check = asyncio.Event()
        self.touch_task = asyncio.create_task(self.touch_check())

        # screen Refresh Management
        self.screen = 0  # 0 = Menu , 1 =  album selector, 2 = Player

        # Refresh Management
        self.refreshCounter = 0
        self.nextRefresh = datetime.now()

    def full_refresh(self):
        self.refreshCounter = 0
        self.epd.init(self.epd.FULL_UPDATE)
        self.epd.displayPartBaseImage(self.epd.getbuffer(self.baseImage))
        self.epd.sleep()
        self.partial_refresh()

    def partial_refresh(self):
        self.refreshCounter += 1
        self.epd.init(self.epd.PART_UPDATE)
        self.epd.displayPartial(self.epd.getbuffer(self.canvas))
        self.epd.sleep()

    def refresh_if_needed(self):
        """refresh screen if necessary."""

        if datetime.now() > self.nextRefresh:
            logging.debug("refresh screen...")
            self.full_refresh()
            # next refresh screen
            self.nextRefresh = datetime.now() + self.full_refresh_delta

        # After multiple partial refresh, do a full refresh
        if self.refreshCounter >= self.partial_update_count:
            self.refreshCounter = 0

    def update_current_track(self, song, album, artist, artwork):
        """update current track."""
        self.canvas.paste(self.player)
        self.draw_song(song, album, artist, artwork)
        self.partial_refresh()

    def draw_song(self, song, album, artist, artwork):
        """draw song information."""
        artwork = artwork.resize((75, 75), Image.Resampling.LANCZOS).convert('1')
        self.canvas.paste(artwork, (2, 2))
        draw = ImageDraw.Draw(self.canvas)
        draw.text((80, 5), song, font=self.font, fill=0)
        draw.text((80, 30), album, font=self.font, fill=0)
        draw.text((80, 55), artist, font=self.font, fill=0)

    def draw_play(self):
        # Define the size and position of the pause button (two vertical bars)
        triangle_size = 21
        # Calculate the position top left
        x = 173
        y = 96

        triangle = [
            (x, y),  # top left
            (x + triangle_size - 3, y + (triangle_size // 2)),  # right
            (x, y + triangle_size),  # bottom
        ]
        background = ((x, y), (x + triangle_size, y + triangle_size))
        # Draw the left and right bars (pause button) with black color
        draw = ImageDraw.Draw(self.canvas)
        draw.rectangle(background, fill='white')
        # Draw the triangle (play button) with black color
        draw.polygon(triangle, fill='black')

    def draw_pause(self):
        """draw pause icon."""
        bar_width = 8
        bar_height = 20
        gap = 5  # Gap between the two bars

        # Calculate the position top left
        x = 173
        y = 96

        right_bar = ((x + gap + bar_width, y), (x + bar_width * 2 + gap, y + bar_height))
        left_bar = ((x, y), (x + bar_width, y + bar_height))
        background = ((x, y), (x + bar_width + gap, y + bar_height))
        draw = ImageDraw.Draw(self.canvas)
        # Draw the left and right bars (pause button) with black color
        draw.rectangle(background, fill='white')
        draw.rectangle(left_bar, fill='black')
        draw.rectangle(right_bar, fill='black')

    def draw_album(self, album, artist, artwork):
        """draw album information."""
        artwork = artwork.resize((75, 75), Image.Resampling.LANCZOS).convert('1')
        self.canvas.paste(artwork, (2, 2))
        draw = ImageDraw.Draw(self.canvas)
        draw.text((80, 20), album, font=self.font, fill=0)
        draw.text((80, 45), artist, font=self.font, fill=0)

    def show_player(self):
        """show player."""
        self.screen = 2
        self.baseImage = self.player
        self.canvas.paste(self.player)
        self.partial_refresh()

    def show_selector(self):
        """show album selector."""
        self.screen = 1
        self.baseImage = self.selector
        self.canvas.paste(self.selector)

        self.partial_refresh()

    def show_menu(self):
        """show menu."""
        self.screen = 0
        self.baseImage = self.menu
        self.canvas.paste(self.menu)
        self.partial_refresh()

    def show_album(self, album, artist, artwork):
        """show album."""
        self.canvas.paste(self.selector)
        self.draw_album(album, artist, artwork)
        self.partial_refresh()

    def show_play_pause(self, is_playing=True):
        if is_playing:
            self.draw_pause()
        else:
            self.draw_play()
        self.partial_refresh()

    def is_on_player_screen(self):
        """return true if player is the current screen."""
        return self.screen == 2

    def read_touch(self):
        """Reads touch inputs and returns the corresponding event."""
        self.gt.GT_Scan(self.GT_Dev, self.GT_Old)

        if self.GT_Old.X[0] == self.GT_Dev.X[0] and self.GT_Old.Y[0] == self.GT_Dev.Y[0]:
            return None

        if self.GT_Dev.TouchpointFlag:

            # reset
            self.GT_Dev.TouchpointFlag = 0
            self.GT_Old.X[0] = self.GT_Dev.X[0]
            self.GT_Old.Y[0] = self.GT_Dev.Y[0]
            self.GT_Old.S[0] = self.GT_Dev.S[0]

            # Menu
            if self.screen == 0:
                if 10 < self.GT_Dev.X[0] < 112 and 10 < self.GT_Dev.Y[0] < 120:
                    return 'selector'
                elif 29 < self.GT_Dev.X[0] < 92 and 140 < self.GT_Dev.Y[0] < 240:
                    return 'player'

            # Sélector
            elif self.screen == 1:
                if 0 <= self.GT_Dev.X[0] <= 75:
                    return 'launch_player'
                elif 80 <= self.GT_Dev.X[0] <= 122 and 160 <= self.GT_Dev.Y[0] <= 210:
                    return 'previous_album'
                elif 80 <= self.GT_Dev.X[0] <= 122 and 100 <= self.GT_Dev.Y[0] <= 150:
                    return 'return_menu'
                elif 80 <= self.GT_Dev.X[0] <= 122 and 40 <= self.GT_Dev.Y[0] <= 90:
                    return 'next_album'

            elif self.screen == 2:
                if 80 <= self.GT_Dev.X[0] <= 122 and 155 <= self.GT_Dev.Y[0] <= 200:
                    return 'return_menu'
                elif 80 <= self.GT_Dev.X[0] <= 122 and 210 <= self.GT_Dev.Y[0] <= 250:
                    return 'selector'
                elif 80 <= self.GT_Dev.X[0] <= 122 and 0 <= self.GT_Dev.Y[0] <= 40:
                    return 'next_track'
                elif 80 <= self.GT_Dev.X[0] <= 122 and 100 <= self.GT_Dev.Y[0] <= 145:
                    return 'previous_track'
                elif 80 <= self.GT_Dev.X[0] <= 122 and 47 <= self.GT_Dev.Y[0] <= 92:
                    return 'play_pause'

    def cleanup(self):
        self.epd.init(self.epd.FULL_UPDATE)
        self.epd.Clear(0xFF)
        self.epd.sleep()

    async def touch_check(self):
        """Touch event management coroutine."""
        while not self.stop_touch_check.is_set():
            if self.gt.digital_read(self.gt.INT) == 0:
                self.GT_Dev.Touch = 1
            else:
                self.GT_Dev.Touch = 0

            await asyncio.sleep(0.05)

    async def stop(self):
        """Stop Touch task"""
        self.stop_touch_check.set()
        await self.touch_task
