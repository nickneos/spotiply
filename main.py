"""
Create a spotify playlist based on the mp3 files in a directory.
"""

import argparse
import logging
import colorlog
import os
import sys
from pathlib import Path
from uuid import uuid4

# my modules
from mltk.genres import clean_tags, scrape_genres
from mltk.spotiply import (
    get_liked_songs,
    get_playlist_items,
    create_spotify_playlist,
    generate_credentials_json,
    spotify_connect,
    get_spotify_track_id,
    music_dir_to_json,
    rbox_to_json,
)

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(THIS_DIR, "data/")


def configure_logger(log_to_screen=False):
    """Setup the logger"""

    # initialise logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # setup formatters
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    color_formatter = colorlog.ColoredFormatter(
        "%(green)s%(asctime)s%(reset)s %(light_black)s%(name)s%(reset)s %(log_color)s%(levelname)s:%(reset)s %(message)s",
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
    )

    # add file handler
    fh = logging.FileHandler("mltk.log", mode="w")
    fh.setFormatter(formatter)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    # add console handler
    if log_to_screen:
        ch = colorlog.StreamHandler()
        ch.setFormatter(color_formatter)
        # ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)

    # other loggers
    loggers = [
        "mltk.spotiply",
        "mltk.genres",
    ]
    for logger_name in loggers:
        _logger = logging.getLogger(logger_name)
        _logger.setLevel(logging.DEBUG)
        _logger.addHandler(fh)
        if log_to_screen:
            _logger.addHandler(ch)

    # logger from other libraries
    logging.getLogger("eyed3").setLevel(logging.ERROR)

    return logger


def parse_args():
    parser = argparse.ArgumentParser(description="Music Library Toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    spotiply = subparsers.add_parser(
        "spotiply",
        help="Create a spotify playlist based on the mp3 files in a directory",
    )
    group1 = spotiply.add_mutually_exclusive_group(required=True)
    group1.add_argument(
        "-cp",
        dest="create_playlist",
        metavar="MUSIC_DIR",
        help="Create spotify playlist based on the mp3 files in MUSIC_DIR",
    )
    group1.add_argument(
        "-j",
        dest="use_json",
        metavar="JSON_FILE",
        help="Create spotify playlist using the json_file passed, instead of a music directory.",
    )
    group1.add_argument(
        "-rb",
        dest="use_rb",
        metavar="REKORDBOX_TXT",
        help="Create spotify playlist using the rekordbox playlist file REKORDBOX_TXT instead of a music directory.",
    )
    group1.add_argument(
        "-c",
        "--credentials",
        action="store_true",
        help="Generate credentials.json file",
    )
    group1.add_argument(
        "-ls",
        "--liked-songs",
        action="store_true",
        help="Generate json of your liked songs.",
    )
    group1.add_argument(
        "--playlist-songs",
        metavar="PLAYLIST_URL",
        help="Generate txt file of the songs from the given spotify playlist PLAYLIST_URL",
    )
    group2 = spotiply.add_argument_group("To be used with --create-playlist")
    group2.add_argument(
        "-dp",
        "--disable-playlist",
        action="store_true",
        help="Will disable creating the actual spotify playlist.",
    )
    group2.add_argument(
        "-p",
        dest="playlist_name",
        type=str,
        help="Name of the playlist you want to create. If not provided will use a uuid.",
    )

    tag_utils = subparsers.add_parser("tag_utils", help="Utilities to clean mp3 tags")
    group3 = tag_utils.add_mutually_exclusive_group(required=True)

    group3.add_argument(
        "-g",
        dest="clean_genres",
        metavar="MUSIC_DIR",
        help="Clean the genres and other tag information for the mp3 files in MUSIC_DIR.",
    )
    group3.add_argument(
        "-ga",
        dest="clean_genres2",
        metavar="MUSIC_DIR",
        help="Clean the genres and other tag information (using artist to determine the genre) for the mp3 files in MUSIC_DIR.",
    )
    group3.add_argument(
        "-ug",
        dest="update_genres",
        action="store_true",
        help="Updates the genre mapping json.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger = configure_logger(log_to_screen=True)

    # create data dir if doesnt exist
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    if args.command == "spotiply":
        sp = spotify_connect()

        if args.credentials:
            generate_credentials_json()

        elif args.liked_songs:
            get_liked_songs(sp)

        elif args.playlist_songs:
            get_playlist_items(sp, args.playlist_songs)

        elif args.create_playlist or args.use_json or args.use_rb:
            playlist_name = args.playlist_name if args.playlist_name else uuid4().hex
            json_file = os.path.join(DATA_DIR, playlist_name + ".json")

            if args.use_json:
                playlist_name = Path(args.use_json).stem
                create_spotify_playlist(sp, playlist_name, args.use_json)
            else:
                if args.use_rb:
                    rbox_to_json(args.use_rb, json_file)
                else:
                    music_dir_to_json(args.create_playlist, json_file)

                get_spotify_track_id(sp, json_file)
                if not args.disable_playlist:
                    create_spotify_playlist(sp, playlist_name, json_file)

    elif args.command == "tag_utils":
        if args.clean_genres:
            clean_tags(args.clean_genres)
        elif args.clean_genres2:
            clean_tags(args.clean_genres2, use_artist_genre=True)
        elif args.update_genres:
            scrape_genres()
