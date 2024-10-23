# MicroPLayer LMS

## Description

This project enables control of a Lyrion Media Server (LMS) player using a Raspberry Pi Zero 
with a Waveshare 2.13" Touch E-Paper display. The interface allows users to view 
and select albums and playlists from Spotify, using the LMS plugin Spotty, which are added to favorites. 
Once an album or playlist is selected, it starts playing, and a playback interface is displayed for controlling the music.


## Features

- Simple graphical interface on the Waveshare E-Paper touchscreen.
- Browse and select Spotify albums and playlists via LMS favorites (using the Spotty plugin).
- Control playback (play/pause, next/previous track).
- Display track information (artist, title, album cover).
- Optimized for Raspberry Pi Zero.

## Hardware Requirements

- **Raspberry Pi Zero W** (or any other compatible Raspberry Pi model).
- **Waveshare 2.13" Touch E-Paper** display.
- A working **Lyrion Media Server (LMS)** on a local network.
- **Spotty plugin** for Spotify integration in LMS.
- Wi-Fi connection for communication between the Raspberry Pi and LMS.

## Prerequisites

Make sure you have the following before you start:

- **Python 3** installed on the Raspberry Pi.
- A working LMS instance with the **Spotty** plugin configured.
- A working LMS PLayer .

## Installation

### 1. Configure the Waveshare 2.13" E-Paper Display

Follow the Waveshare documentation to install the necessary drivers and set up the E-Paper display on your Raspberry Pi.

- [Waveshare 2.13" Touch E-Paper Documentation](https://www.waveshare.com/wiki/2.13inch_Touch_e-Paper_HAT_Manual#Raspberry_Pi)

### 2. Clone the Project Repository

```bash
git clone https://github.com/your-username/project-name.git
cd project-name
```
### 3. Install the Required Dependencies

Install the required Python libraries by running:
```bash
pip install -r requirements.txt
```

### 4. Setup LMS and Spotty

- Ensure LMS is installed and running on your local network.
- Install the Spotty plugin and link it to your Spotify account.
- Add your favorite albums and playlists in Spotify, so they are accessible through the interface.

### Configuration

The application can be configured through environment variables. These variables are used to customize the behavior of the player and its connection to the LMS and Spotify.

Here are the environment variables used in the config.py file:

- LMS_SERVER: The IP address or hostname of the Logitech Media Server (default: 192.168.0.29).
- PLAYER_NAME: The name of the LMS player to control (default: default).
- SPOTIFY_USER: Spotify username for the Spotty plugin (default: default).
- PARTIAL_UPDATE_COUNT: Number of partial screen updates before a full refresh of the E-Paper display (default: 100).
- FULL_REFRESH_TIME: Interval in seconds for a full screen refresh (default: 12 seconds).
- LOG_LEVEL: Logging level for the application (default: INFO).

Example of setting environment variables in the shell:
```bash
export LMS_SERVER="192.168.1.100"
export PLAYER_NAME="livingroom"
export SPOTIFY_USER="YourSpotifyUsername"
export LOG_LEVEL="INFO"
```

You can set these environment variables either directly in your shell or create a .env file in your project directory to override the default settings.

Example of setting environment variables in the shell:

## Usage

1. Run the main Python script on your Raspberry Pi:
    ```bash
    python3 run.py
    ```

2. Use the touchscreen to navigate through your favorite Spotify albums and playlists.
3. Select an album or playlist to start playback.
4. The music player interface will display, allowing you to control playback.
