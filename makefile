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
.PHONY: help sync sync-desktop sync-laptop sync-work
help:
	@echo "Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo "Options: ADDITIONAL_FLAGS=\"--list of --additional --flags\"; pass in additional flags to uv download musicdownloader"

sync:				## Usage: make sync PLAYLIST_DIR=[DIR]. Syncs a given folder containing playlists
	test -d "$(PLAYLIST_DIR)" && cd "$(PLAYLIST_DIR)" && git pull 
	uv run musicdownloader --location "$(PLAYLIST_DIR)" \
		--cookies-from-browser firefox \
		--check-metadata-changes \
		--check-quality-increase \
		$(ADDITIONAL_FLAGS)
		



sync-desktop:		## sync music files for my desktop
	$(MAKE) sync PLAYLIST_DIR="$(HOME)/Music/My Music" ADDITIONAL_FLAGS=$(ADDITIONAL_FLAGS)


LAPTOP_PLAYLIST_DIR := "/mnt/D/Music/My Music"
ifeq ($(OS),Windows_NT)
	LAPTOP_PLAYLIST_DIR := "D:\Music\My Music"
endif

sync-laptop:		## sync music files for my laptop. Works on both Linux and Windows, for my laptop in specific. Would recommend running on Linux over windows.
	@echo "Using directory: " $(LAPTOP_PLAYLIST_DIR)
	$(MAKE) sync PLAYLIST_DIR=$(LAPTOP_PLAYLIST_DIR) ADDITIONAL_FLAGS=$(ADDITIONAL_FLAGS)

sync-work:			## sync music files for my work computer
	$(MAKE) sync PLAYLIST_DIR="$(HOME)/Music" ADDITIONAL_FLAGS=$(ADDITIONAL_FLAGS)