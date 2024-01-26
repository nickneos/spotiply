"""
Create a spotify playlist based on the mp3 files in a directory.
"""

import argparse
import os
from pathlib import Path
from mltk.spotiply import *
from mltk.genres import clean_tags
from uuid import uuid4

THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def do_stuff(args):

    if args.credentials:
        generate_credentials_json()
    
    elif args.clean_tags:
        clean_tags(args.clean_tags)

    elif args.liked_songs or args.liked_songs_urls:
        get_liked_songs(sp, json_file, urls=args.liked_songs_urls)

    elif args.create_playlist or args.use_json:
        playlist_name = uuid4().hex if args.playlist_name else args.playlist_name
        json_file = os.path.join(THIS_DIR, "..", "data", playlist_name + ".json")
        sp = spotify_connect()

        # create data dir if doesnt exist 
        p = Path(json_file).parent
        p.mkdir(parents=True, exist_ok=True)

        if args.use_json:
            playlist_name = Path(args.use_json).stem
            create_spotify_playlist(sp, playlist_name, args.use_json)
        else:
            music_dir_to_json(path, json_file)
            get_spotify_track_id(sp, json_file)
            if not args.disable_playlist:
                create_spotify_playlist(sp, playlist_name, json_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="spotiply",
        description="Create a spotify playlist based on the mp3 files in a directory.",
    )
    # group1 = parser.add_mutually_exclusive_group(required=False)
    parser.add_argument(
        "-c",
        "--credentials",
        dest="credentials",
        action="store_true",
        help="Generate credentials.json file",
    )
    group1 = parser.add_argument_group()
    group1.add_argument(
        "-cp",
        "--create-playlist",
        dest="create_playlist",
        metavar="MUSIC_DIR",
        help="Create spotify playlist based on the mp3 files in MUSIC_DIR",
    )
    group1.add_argument(
        "-dp",
        "--disable-playlist",
        dest="disable_playlist",
        action="store_true",
        help="Do all tasks, except creating the actual spotify playlist",
    )
    group1.add_argument(
        "-p",
        "--playlist-name",
        dest="playlist_name",
        type=str,
        help="Name of the playlist you want to create. If not provided will use a uuid.",
    )
    parser.add_argument(
        "-j",
        "--use-json",
        dest="use_json",
        metavar="JSON_FILE",
        help="Create spotify playlist using the json_file passed, instead of a music directory.",
    )
    parser.add_argument(
        "-ls",
        "--liked-songs",
        dest="liked_songs",
        action="store_true",
        help="Generate json of your liked songs.",
    )
    parser.add_argument(
        "--liked-songs-urls",
        dest="liked_songs_urls",
        action="store_true",
        help="Generate txt file of the urls of your liked songs.",
    )
    parser.add_argument(
        "--clean-tags",
        dest="clean_tags",
        metavar="MUSIC_DIR",
        help="Clean the tag information for mp3 files in MUSIC_DIR.",
    )

    parser.set_defaults(func=do_stuff)

    args = parser.parse_args()
    args.func(args)
