
import threading
import time
import sys
import os
import select

from .config import MDappConfig
from .backend import MDapp

Mock_config = MDappConfig(
    playlist_folders=["playlist"],
    shuffle=True,
    songs_before_reshuffle=1,
    play_subplaylists=True,
    last_played=None,
)


if os.name == "nt":
    import msvcrt

    def get_key():
        if msvcrt.kbhit():
            return msvcrt.getwch()
        return None

else:
    import termios
    import tty

    def get_key():
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None


def update_line(line: int, text: str):
    sys.stdout.write(f"\033[{line};1H\033[2K{text}")


def run_cli():
    app = MDapp(Mock_config)
    command = ""
    error_message = ""

    # Save terminal settings on Unix
    old_settings = None

    try:
        if os.name != "nt":
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)

        # Initialize terminal
        sys.stdout.write("\033[?1049h")  # Alternate screen
        sys.stdout.write("\033[?25l")    # Hide cursor
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        running = True

        while running:
            # --- RENDERING ---

            update_line(1, f"{error_message}Playing: {app.current_song}")

            if app.current_song_time is not None and app.current_song_length:
                length = 70
                percent = app.current_song_time / app.current_song_length
                percent = max(0, min(percent, 1))

                filled = int(length * percent)
                progress = "#" * filled + "-" * (length - filled)

                pstring = " - paused" if app.player.paused else ""

                update_line(2, f"[{progress}]{pstring} {app.current_song_time:.1f}s")
            else:
                update_line(2, "No playback")

            # Input line
            update_line(3, f"> {command}")

            # Position cursor after current input
            sys.stdout.write(f"\033[3;{len(command) + 4}H")
            sys.stdout.flush()

            # --- INPUT HANDLING ---

            key = get_key()

            if key is not None:
                if key in ("\r", "\n"):
                    u = command.split()
                    command = ""
                    error_message = ""

                    if u:
                        error_message = ""
                        match u[0]:
                            case "t":
                                app.toggle_pause_play()

                            case "n":
                                app.play_next()

                            case "p":
                                app.play_prev()

                            case "s":
                                try:
                                    app.set_to(float(u[1]))
                                except ValueError:
                                    error_message = "Please enter a valid float - "
                                except IndexError:
                                    error_message = "Please enter a number - "

                            case _:
                                error_message = "Unrecognized command - "

                elif key in ("\x7f", "\b"):
                    command = command[:-1]

                elif key == "\x03":
                    running = False

                elif len(key) == 1 and key.isprintable():
                    command += key

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass

    finally:
        # Restore terminal settings
        if old_settings is not None:
            termios.tcsetattr(
                sys.stdin.fileno(),
                termios.TCSADRAIN,
                old_settings
            )

        sys.stdout.write("\033[?25h")    # Show cursor
        sys.stdout.write("\033[?1049l")  # Restore original screen
        sys.stdout.flush()
