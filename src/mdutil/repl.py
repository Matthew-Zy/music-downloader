from pathlib import Path

from . import extract_playlist

            



def run_repl(output: Path | None):
    def run_command(argv: list[str]):
        if len(argv) < 1:
            return 
        nonlocal output
        match argv[0]:
            case "help":
                print("Help commands for the mdutil repl")
            case "output":
                output = Path(argv[1]) if len(argv) >= 2 else None
            case _: 
                extract_playlist.yt_music_tracks_to_toml(argv[0], output)
    try:
        while True:
            x = input("> ").strip().split()
            run_command(x)
    except KeyboardInterrupt:
        print("\nGoodbye")