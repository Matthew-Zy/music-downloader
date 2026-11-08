from pathlib import Path
from dataclasses import dataclass 
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


class MDutilRepl:
    @dataclass
    class ReplCmd:
        cmd: callable[MDutilRepl, list[str]]
        help: str 
    output: Path 
    commands: dict[str, ReplCmd]

    def __init__(self, output: Path | None):
        self.output = output
        self.commands = {
            "help" : self.ReplCmd(self.cmd_print_help, "Prints help for the repl and available commands"),
            "output" : self.ReplCmd(self.cmd_set_output, "Usage: output [output file]. Sets the output of any commands we use. Do not specify an output file for None")
        }

    def cmd_print_help(self, argv: list[str]):
        for i, v in self.commands.items():
            print(f"{i}; {v.help}")
        pass

    def cmd_set_output(self, argv: list[str]):
        try:
            self.output = Path(argv[1])
            print(f"Output set to: {self.output}")
        except IndexError:
            self.output = None
            print("Output set to None")
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
                argv_at_home: list[str] = input("> ").strip().split()
                self.execute_command(argv_at_home)
        except KeyboardInterrupt:
            print("Goodbye!")
