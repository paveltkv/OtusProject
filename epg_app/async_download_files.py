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

FILES_PATH = "epg_data"
FOLDERS_PATH = "epg_app/static/logos/"


@dataclass
class EPGService:
    name: str
    url: str


def get_file_path(pk: int, name: str, url: str, is_epg: bool) -> str:
    data_type = "epg"
    if is_epg is False:
        data_type = "logos"
    return os.path.join(FILES_PATH, str(pk) + "-" + data_type + "." + name + "." + url.split("/")[-1])


def get_folder_name(pk: int, name: str, url: str) -> str:
    return os.path.join(FOLDERS_PATH, str(pk) + "-" + name + "." + url.split("/")[-1])


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()


def download_files(urls: list[dict], update_success_callback, update_error_callback):
    os.makedirs(FILES_PATH, exist_ok=True)

    print("URLS: ", urls)

    async def fetch_file(epg_service):
        print("epg_service: ", epg_service)
        f_name = get_file_path(epg_service['pk'], epg_service['name'], epg_service['url'], epg_service['is_epg'])

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(epg_service['url']) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        async with aiomisc.io.async_open(
                                f_name, "wb"
                        ) as outfile:
                            print("Write:", f_name, sys.getsizeof(data))
                            await outfile.write(data)

                        print("OK:", epg_service, ", size:", sys.getsizeof(data))
                        update_success_callback(epg_service, sys.getsizeof(data))
                    else:
                        pass
                        update_error_callback(epg_service, f"status code error: {resp.status}")

        except aiohttp.InvalidURL as e:
            update_error_callback(epg_service, f"invalid URL: {e}")
        except aiohttp.ClientConnectorError:
            update_error_callback(epg_service, "unreachable")
        except aiohttp.ServerDisconnectedError as e:
            update_error_callback(epg_service, f"server disconnected: {e}")
        except aiohttp.ClientOSError as e:
            update_error_callback(epg_service, f"client OS error: {e}")
        except aiohttp.TooManyRedirects as e:
            update_error_callback(epg_service, f"too many redirects: {e}")
        except aiohttp.ClientResponseError as e:
            update_error_callback(epg_service, f"client response: {e}")
        except aiohttp.ServerTimeoutError:
            update_error_callback(epg_service, "connection timeout")
        except asyncio.TimeoutError:
            update_error_callback(epg_service, "connection timeout")
        except aiohttp.ClientError as e:
            update_error_callback(epg_service, f"client error: {e}")

    loop = asyncio.new_event_loop()
    tasks = [loop.create_task(fetch_file(epg_service)) for epg_service in urls]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()


def extractall_to_static(epg: Epg):
    print("START")

    file_path = get_file_path(epg.pk, epg.name, epg.logos_url, is_epg=False)
    folder_path = get_folder_name(epg.pk, epg.name, epg.logos_url)

    file_format = epg.logos_url.split("/")[-1].split(".")[-1]

    if file_format == "zip":
        with zipfile.ZipFile(file_path, 'r') as zipObj:
           zipObj.extractall(folder_path)
