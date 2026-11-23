

from .config import MDappConfig
from .backend import MDapp

Mock_config = MDappConfig(
    playlist_folders = ["playlist"],
    shuffle=True,
    songs_before_reshuffle=1,
    play_subplaylists=True,
    last_played=None, 
)


def run_cli():
    app = MDapp(Mock_config)

    try:
        while True:
            u = input("> ")
            match u:
                case "t":
                    app.toggle_pause_play()
                case "n":
                    app.play_next()
                case _:
                    print("unrecognized")

    except KeyboardInterrupt:
        print("Adios")