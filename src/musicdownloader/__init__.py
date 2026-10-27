from argparse import ArgumentParser, ArgumentError, ArgumentDefaultsHelpFormatter
from pathlib import Path 

from . import config
from . import musicloader


def is_valid_folder_or_file(path):
    if Path(path).exists():
        return path 
    else:
        raise ArgumentError("File path does not exists")

def parse_args() -> dict[str, any]:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, description="Downloads music from a toml file containing information", epilog="e")
    parser.add_argument("-l", "--location", type=Path, default=config.DEFAULT_FILE_LOCATION, help="File/Folder to load songs to download from")
    parser.add_argument("-sf", "--save-file", type=Path, default=config.DEFAULT_PREV_STORE_LOCATION, help="File to use from a previous download to prevent duplicate downloads, file to write to after download. If a custom file/folder is passed through -l/--location, it will default to ${location}/${location}-downloaded.json if folder, and ${location}-downloaded.json if file.")
    parser.add_argument("-ol", "--output-folder", type=Path, default=config.DEFAULT_OUTPUT_FOLDER, help="Folder to save songs to. If a custom location is provided, it will default to ${location}/${location}")
    parser.add_argument("--all", type=bool, default=config.DEFAULT_DOWNLOAD_ALL, help="Download all songs from given location instead of downloading undownloaded songs")
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
        help="Browser cookies, e.g. firefox or chrome:Profile 1",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    print(args)
    print("Hello from musicdownloader!")
    configuration: config.DownloadConfig = config.DownloadConfig(
        download_all=args.all,
        output_folder=args.output_folder,
        max_tries=args.retries,

    )
    print(configuration)
    return
    x = musicloader.read_music_file_toml(args.location)
    musicloader.write_music_file_json(args.save_file, x)
