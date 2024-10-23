import asyncio
import logging

from micro_player import config
from micro_player.micro_player import main

logging.basicConfig(level=config.LOG_LEVEL)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as me:
        logging.error(f"Unexpected error : {me}")