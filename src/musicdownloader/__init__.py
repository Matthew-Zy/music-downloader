from argparse import ArgumentParser, ArgumentError, ArgumentDefaultsHelpFormatter, BooleanOptionalAction
from pathlib import Path 
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event, Lock

from yt_dlp.globals import all_plugins_loaded
from yt_dlp.plugins import load_all_plugins

from . import config
from . import musicloader
from . import download_songs

def to_d_format(p: Path) -> Path:
    return p.parent / f"{p.stem}-downloaded.json"

def parse_args() -> dict[str, any]:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, description="Downloads music from a toml file containing information", epilog="e")
    parser.add_argument("-l", "--location", type=Path, default=config.DEFAULT_FILE_LOCATION, help="File/Folder to load songs to download from")
    parser.add_argument("-sf", "--save-file", type=Path, default=config.DEFAULT_PREV_STORE_LOCATION, help="File to use from a previous download to prevent duplicate downloads, file to write to after download. If a custom file/folder is passed through -l/--location, it will default to ${location}/${location}-downloaded.json if folder, and ${location}-downloaded.json if file.")
    parser.add_argument("-ol", "--output-folder", type=Path, default=config.DEFAULT_OUTPUT_FOLDER, help="Folder to save songs to. If a custom location is provided, it will default to ${location}/${location}")
    parser.add_argument("--all", action='store_true', dest="all", default=config.DEFAULT_DOWNLOAD_ALL, help="Download all songs from given location instead of downloading undownloaded songs")
    parser.add_argument(
        "--check-quality-increase",
        action=BooleanOptionalAction,
        default=config.DEFAULT_CHECK_QUALITY_INCREASE,
        help="Check previously downloaded songs for quality upgrades (ignored with --all)",
    )
    parser.add_argument("-r", "--retries", type=int, default=config.DEFAULT_MAX_TRIES, help="Maximum retries for failing to download a song")
    
    cookies = parser.add_mutually_exclusive_group()
    cookies.add_argument(
        "-c", "--cookies",
        type=str,
        help="Path to a Netscape cookies.txt file",
    )
    cookies.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER[:PROFILE]",
        default=config.DEFAULT_COOKIES_BROWSER,
        help="Browser cookies, e.g. firefox or chrome:Profile 1",
    )
    args = parser.parse_args()
    if args.cookies is not None:
        args.cookies_from_browser = None
    return args


def download_from_source_file(source_location: Path, save_location: Path, configuration: config.DownloadConfig, *, cancel_event: Event | None = None):
    try: 
        to_download = musicloader.read_music_file_toml(source_location)
    except FileNotFoundError:
        print(f"Could not find given file: {source_location}")
        return
    try:
        prev_downloaded = musicloader.read_music_file_json(save_location)
    except FileNotFoundError:
        prev_downloaded = []
    just_downloaded = download_songs.download_songs(
        to_download, prev_downloaded, configuration, cancel_event=cancel_event,
    )
    musicloader.write_music_file_json(save_location, just_downloaded)

def download_from_source_folder(args: dict[str, any]):
    source_folder: Path = Path(args.location)
    cancel_event = Event()
    output_locks = {}

    def download_file(source, output_lock):
        # Files in the same directory share audio paths, so serialize them.
        while not cancel_event.is_set():
            if output_lock.acquire(timeout=0.1):
                break
        else:
            return
        try:
            if cancel_event.is_set():
                return
            configuration = config.DownloadConfig(
                download_all=args.all,
                check_quality_increase=args.check_quality_increase,
                output_folder=source.parent,
                max_tries=args.retries,
                cookies=args.cookies,
                browser_cookies=args.cookies_from_browser,
            )
            download_from_source_file(
                source, to_d_format(source), configuration, cancel_event=cancel_event,
            )
        finally:
            output_lock.release()

    # yt-dlp's lazy plugin registration uses shared state without a lock.
    # Complete it on the main thread before workers construct YoutubeDL.
    if not all_plugins_loaded.value:
        load_all_plugins()

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        try:
            directories = [source_folder]
            visited = set()
            while directories:
                directory = directories.pop()
                resolved = directory.resolve()
                if resolved in visited:
                    continue
                visited.add(resolved)
                for source in directory.iterdir():
                    if source.is_dir():
                        directories.append(source)
                    elif source.is_file() and source.suffix == ".toml":
                        output_lock = output_locks.setdefault(source.parent.resolve(), Lock())
                        futures.append(executor.submit(download_file, source, output_lock))
            for future in as_completed(futures):
                future.result()
        except KeyboardInterrupt:
            cancel_event.set()
            for future in futures:
                future.cancel()
            print("\nStopping downloads and saving completed records...")
        # Executor shutdown waits for active workers to save their records.

def main() -> None:
    args = parse_args()
    if Path(args.location).is_file():
        print(args)
        configuration: config.DownloadConfig = config.DownloadConfig(
            download_all=args.all,
            check_quality_increase=args.check_quality_increase,
            output_folder=args.output_folder,
            max_tries=args.retries,
            cookies=args.cookies,
            browser_cookies=args.cookies_from_browser,
        )
        download_from_source_file(args.location, args.save_file, configuration)
    elif Path(args.location).is_dir():
        download_from_source_folder(args)
    else:
        print(f'Given path: "{args.location}" does not exists')
