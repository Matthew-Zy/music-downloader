import argparse 
from pathlib import Path

from . import extract_playlist
from . import rm_audio 




def parse_args() -> dict[str, any]:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="",
        epilog="Riyal or Fakeh"           
    )

    parser.add_argument("-ep", "--extract-playlist", type=str, default=None, 
        help="Turn a PUBLIC yt playlist into a valid TOML configuration. Outputs it to the given output if provided, otherwise just prints it to console. Appends it to the existing toml file if it already exists. For duplicates, it will use the existing toml file's entry instead.")
    parser.add_argument("-o", "--output", type=Path, default=None, 
        help="output location for any operations")
    parser.add_argument("-rm", "--remove-music", type=Path, default=None, 
        help=f"Delete all music files from a folder. (Files that will be deleted: {rm_audio.AUDIO_EXTENSIONS})")
    return parser.parse_args()


def main():
    args = parse_args()
    print(args)

    if args.extract_playlist:
        if "youtube" in args.extract_playlist.lower():
            extract_playlist.yt_music_tracks_to_toml(args.extract_playlist, args.output)
        elif "spotify" in args.extract_playlist.lower():
            print("Implementation for spotify does not exist yet.... (TBD)")

    if args.remove_music:
        rm_audio.rm_audio(args.remove_music)