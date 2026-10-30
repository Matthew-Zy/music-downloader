import argparse 
import os
import sys
from pathlib import Path

from . import extract_playlist
from . import audio_funcs 


def print_to_terminal(message):
    # Use 'CON' for Windows and '/dev/tty' for Unix/Linux/macOS
    tty_device = 'CON' if os.name == 'nt' else '/dev/tty'
    
    try:
        with open(tty_device, 'w', encoding='utf-8') as tty:
            tty.write(message + '\n')
    except OSError:
        # Fallback to stderr if there is no controlling terminal 
        # (e.g., in a background cron job or some CI/CD pipelines)
        sys.stderr.write(message + '\n')


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
        help=f"Delete all music files from a folder. (Files that will be deleted: {audio_funcs.AUDIO_EXTENSIONS})")
    parser.add_argument("-ls", "--playlist-sizes", type=Path, default=None, 
        help="List the playlist sizes of a playlist or all playlists in a folder.")
    return parser.parse_args()


def main():
    actions = 0
    args = parse_args()
#    print(args)

    if args.extract_playlist:
        if "youtube" in args.extract_playlist.lower():
            extract_playlist.yt_music_tracks_to_toml(args.extract_playlist, args.output)
        elif "spotify" in args.extract_playlist.lower():
            print("Implementation for spotify does not exist yet.... (TBD)")
        else:
            print(f"'{args.extract_playlist}' is not a valid/supported playlist.")
        actions += 1

    if args.remove_music:
        audio_funcs.rm_audio(args.remove_music)
        actions += 1
    if args.playlist_sizes:
        audio_funcs.playlist_lengths(args.playlist_sizes)
        actions += 1

    if actions <= 0:
        print_to_terminal(f"{actions} actions completed, please use -h or --help for help")
    else:
        print_to_terminal(f"Completed {actions} action(s)")