from pathlib import Path
from dataclasses import dataclass 
import shlex, os

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

@dataclass
class ReplCmd:
    cmd: callable[MDutilRepl, list[str]] | callable[list[str]]
    help: str 

class MDutilRepl:
    output: Path 
    commands: dict[str, ReplCmd]

    def __init__(self, output: Path | None):
        self.output = output
        self.commands = {
            "help" : ReplCmd(self.cmd_print_help, "Prints help for the repl and available commands"),
            "output" : ReplCmd(self.cmd_set_output, "Usage: output [output file]. Sets the output of any commands we use. Do not specify an output file for None"),
            "cwd" : ReplCmd(self.cmd_cwd, "Usage: cwd [path]. Changes the current working directory to a new given path"),
            "pwd" : ReplCmd(lambda _: print(os.getcwd()), "Prints the current working directory of the repl"),
            "clear": ReplCmd(lambda _: print("\x1b[2J\x1b[3J\x1b[H"), "clears the terminal")
        }

################### Repl commands here
    def cmd_print_help(self, argv: list[str]):
        print("Available commands:")
        longest_key = max(self.commands, key=len)
        width = len(longest_key)
        for i, v in self.commands.items():
            print(f"{i:<{width}} : {v.help}")
        pass

    def cmd_set_output(self, argv: list[str]):
        try:
            self.output = Path(argv[1])
            print(f"Output set to: {self.output}")
        except IndexError:
            self.output = None
            print("Output set to None")

    # coreutils at home
    def cmd_cwd(self, argv: list[str]):
        try:
            os.chdir(argv[1])
            print(f"Changed working directory to: {os.getcwd()}")
        except IndexError:
            print("Please enter a working directory")
            print(f"Working directory remains unchanged ({os.getcwd()})")
        except FileNotFoundError:
            print(f"Working directory: {Path(argv[1]).absolute()} does not exist")
        except OSError:
            print(f"Error changing working directory to: {argv[1]}")


################### Repl commands end here

    def execute_command(self, argv: list[str]):
        if len(argv) < 1:
            return 

        cmd = self.commands.get(argv[0])
        if cmd is None:
            try:
                extract_playlist.yt_music_tracks_to_toml(argv[0], self.output)
            except TypeError as e:
                print(f"Error failed when getting playlist information: {e}")
                print("Your provided url was most likely faulty or the program can't access youtube's servers right now!")
            except Exception as e:
                print(f"Error failed when getting playlist information: {e}")
            return 
        argv[0] = argv[0].lower()
        cmd.cmd(argv)




    
    def run_repl(self):
        print("Use Control+C to exit; enter help for help")
        try:
            while True:
                argv_at_home: list[str] = shlex.split(input("> "))

                self.execute_command(argv_at_home)
        except KeyboardInterrupt:
            print("Goodbye!")
