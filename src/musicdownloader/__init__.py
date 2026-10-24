from argparse import ArgumentParser, ArgumentError, ArgumentDefaultsHelpFormatter
from pathlib import Path 

from . import config



def is_valid_folder_or_file(path):
    if Path(path).exists():
        return path 
    else:
        raise ArgumentError("File path does not exists")

def parse_args() -> dict[str, any]:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, description="Downloads music from a toml file containing information", epilog="e")
    parser.add_argument("-l", "--location", type=Path, default=config.DEFAULT_FILE_LOCATION, help="File/Folder to load songs to download from")
    parser.add_argument("-ol", "--output-location", type=Path, default=config.DEFAULT_OUTPUT_LOCATION, help="Folder to save songs to")
    parser.add_argument("--all", type=bool, default=config.DEFAULT_DOWNLOAD_ALL, help="Download all songs from given location instead of downloading undownloaded songs")

    return parser.parse_args()
def main() -> None:
    args = parse_args()
    print(args)
    print("Hello from musicdownloader!")
