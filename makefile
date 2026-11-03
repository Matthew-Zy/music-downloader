#
# How it feels to chew 5 gum.
#

ifeq ($(HOME),)
    HOME := $(USERPROFILE)
endif

# Fix backslashes for cross-platform safety in Make commands
HOME := $(subst \,/,$(HOME))
PLAYLIST_DIR := music
ADDITIONAL_FLAGS := ""

ifeq ($(OS),Windows_NT)

endif

.PHONY: help sync sync-desktop sync-laptop sync-work
help: ## Show available commands
	@python help.py "$(MAKEFILE_LIST)"
	@echo Options: ADDITIONAL_FLAGS="--list of --additional --flags", pass in additional flags to uv download musicdownloader
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
		--cookies-from-browser firefox \
		$(ADDITIONAL_FLAGS)



sync-desktop:		## sync music files for my desktop
	$(MAKE) sync PLAYLIST_DIR="$(HOME)/Music/My Music" ADDITIONAL_FLAGS=$(ADDITIONAL_FLAGS)

WINDOWS_LAPTOP_PLAYLIST_DIR := "D:\Music\My Music"
LAPTOP_PLAYLIST_DIR := "/mnt/D/Music/My Music"
ifeq ($(OS),Windows_NT)
	LAPTOP_PLAYLIST_DIR := $(WINDOWS_LAPTOP_PLAYLIST_DIR)
endif

sync-laptop:		## sync music files for my laptop. Works on both Linux and Windows, for my laptop in specific. Would recommend running on Linux over windows.
	@echo "Using directory: " $(LAPTOP_PLAYLIST_DIR)
	$(MAKE) sync PLAYLIST_DIR=$(LAPTOP_PLAYLIST_DIR) ADDITIONAL_FLAGS=$(ADDITIONAL_FLAGS)

sync-work:			## sync music files for my work computer
	$(MAKE) sync PLAYLIST_DIR="$(HOME)/Music" ADDITIONAL_FLAGS=$(ADDITIONAL_FLAGS)