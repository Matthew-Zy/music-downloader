#
# How it feels to chew 5 gum.
#

ifeq ($(HOME),)
    HOME := $(USERPROFILE)
endif

# Fix backslashes for cross-platform safety in Make commands
HOME := $(subst \,/,$(HOME))
PLAYLIST_DIR := music
BROWSER_COOKIES ?= firefox
FLAGS := 

ifeq ($(OS),Windows_NT)
# What am I even doing 
# Sigma ohio skibidi Rizzler Sigma Ohio
endif

define DETAILED_HELP_SCRIPT
import re

commands = []

with open("makefile", encoding="utf-8") as f:
    for line in f:
        # Note the double $$ at the end of the regex string
        match = re.match(r"^([a-zA-Z_-]+):.*?## (.*)$$", line)
        if match:
            commands.append(match.groups())

print("Available Commands:")

for name, description in sorted(commands):
    print(f"\033[36m{name:<15}\033[0m {description}")
endef
export DETAILED_HELP_SCRIPT

.PHONY: help sync sync-desktop sync-laptop sync-work
help: ## Show available commands
	@python -c "import os; exec(os.environ['DETAILED_HELP_SCRIPT'])"
	@echo 'Options: FLAGS=\"--list of --additional --flags\"; pass in additional flags to musicdownloader'
	@echo Home directory: ${HOME}

# Cleaning commands to fix some random fuckass character in nodriver/cdp/network.py library
# will 100% be removed after nodriver publishes a release to pypi that gets rid of that comment
# From what I see, it's been removed from the main branch already...
CLEAN_SCRIPT := "./fix-pkg-encoding.sh"
ifeq ($(OS),Windows_NT)
	CLEAN_SCRIPT := powershell -File fix-pkg-encoding.ps1
endif

sync:				## Usage: make sync PLAYLIST_DIR=[DIR]. Syncs a given folder containing playlists
	$(CLEAN_SCRIPT)
	cd "$(PLAYLIST_DIR)" && git pull 
	uv run musicdownloader --location "$(PLAYLIST_DIR)" \
		--cookies-from-browser $(BROWSER_COOKIES) \
		$(FLAGS)



sync-desktop:		## sync music files for my desktop (which runs windows)
	$(MAKE) sync PLAYLIST_DIR="$(HOME)\\Music\\My Music" FLAGS=$(FLAGS)

WINDOWS_LAPTOP_PLAYLIST_DIR := "D:\Music\My Music"
LAPTOP_PLAYLIST_DIR := "/mnt/D/Music/My Music"
ifeq ($(OS),Windows_NT)
	LAPTOP_PLAYLIST_DIR := $(WINDOWS_LAPTOP_PLAYLIST_DIR)
endif

sync-laptop:		## sync music files for my laptop. Works on both Linux and Windows, for my laptop in specific. Would recommend running on Linux over windows.
	@echo "Using directory: " $(LAPTOP_PLAYLIST_DIR)
	$(MAKE) sync PLAYLIST_DIR=$(LAPTOP_PLAYLIST_DIR) FLAGS=$(FLAGS)

sync-work:			## sync music files for my work computer (which runs linux)
	$(MAKE) sync PLAYLIST_DIR="$(HOME)/Music" FLAGS=$(FLAGS)