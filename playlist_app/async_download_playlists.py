import os
import asyncio
import sys

import aiohttp  # pip install aiohttp
import aiomisc  # pip install aiofile
from dataclasses import dataclass
import zipfile

# REPORTS_FOLDER = "reports"
# FILES_PATH = os.path.join(REPORTS_FOLDER, "files")
from epg_app.models import Epg


def download_playlists(urls: list[dict], update_success_callback, update_error_callback):
    print("URLS: ", urls)

    async def fetch_file(playlist):
        print("playlist: ", playlist)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(playlist['url']) as resp:
                    if resp.status == 200:
                        data = await resp.read()

                        print("OK:", playlist, ", size:", sys.getsizeof(data))
                        update_success_callback(playlist, data.decode('utf-8'))
                    else:
                        update_error_callback(playlist, f"status code error: {resp.status}")

        except aiohttp.InvalidURL as e:
            update_error_callback(playlist, f"invalid URL: {e}")
        except aiohttp.ClientConnectorError:
            update_error_callback(playlist, "unreachable")
        except aiohttp.ServerDisconnectedError as e:
            update_error_callback(playlist, f"server disconnected: {e}")
        except aiohttp.ClientOSError as e:
            update_error_callback(playlist, f"client OS error: {e}")
        except aiohttp.TooManyRedirects as e:
            update_error_callback(playlist, f"too many redirects: {e}")
        except aiohttp.ClientResponseError as e:
            update_error_callback(playlist, f"client response: {e}")
        except aiohttp.ServerTimeoutError:
            update_error_callback(playlist, "connection timeout")
        except asyncio.TimeoutError:
            update_error_callback(playlist, "connection timeout")
        except aiohttp.ClientError as e:
            update_error_callback(playlist, f"client error: {e}")

    loop = asyncio.new_event_loop()
    tasks = [loop.create_task(fetch_file(epg_service)) for epg_service in urls]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
