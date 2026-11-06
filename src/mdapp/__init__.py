import time

from just_playback import Playback 

def main():
    playback = Playback() # creates an object for managing playback of a single audio file
    playback.load_file('playlist/Sukiyo.opus')
    playback.play() 

    print(playback.duration)
    playback.seek(3000)
    try:
        while True:
            x = input()
    except KeyboardInterrupt:
        pass 