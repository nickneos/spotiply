"""
Create a spotify playlist based on the mp3 files in a directory.
"""

import argparse
import os
from pathlib import Path
from spotiply import *
from uuid import uuid4

THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def do_stuff(args):
    if args.credentials:
        generate_credentials_json()
    else:
        path = "." if args.music_dir == "" else args.music_dir
        playlist_name = uuid4().hex if args.playlist_name == "" else args.playlist_name
        json_file = os.path.join(THIS_DIR, "..", "data", playlist_name + ".json")

        # create data dir if doesnt exist 
        p = Path(json_file).parent
        p.mkdir(parents=True, exist_ok=True)

        if args.use_json:
            playlist_name = Path(args.use_json).stem
            create_spotify_playlist(playlist_name, args.use_json)
        else:
            music_dir_to_json(path, json_file)
            get_spotify_track_id(json_file)
            if not args.disable_playlist:
                create_spotify_playlist(playlist_name, json_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="spotiply",
        description="Create a spotify playlist based on the mp3 files in a directory.",
    )
    parser.add_argument(
        "music_dir",
        type=str,
        help="Full path of the music directory.",
        nargs="?",
        default="",
    )
    parser.add_argument(
        "playlist_name",
        type=str,
        help="Name of the playlist you want to create. If not provided will use a uuid.",
        nargs="?",
        default="",
    )
    group1 = parser.add_mutually_exclusive_group(required=False)
    group1.add_argument(
        "-c",
        "--credentials",
        dest="credentials",
        action="store_true",
        help="Generate credentials.json file",
    )
    group1.add_argument(
        "-dp",
        "--disable-playlist",
        dest="disable_playlist",
        action="store_true",
        help="Do all tasks, except creating the actual spotify playlist",
    )
    group1.add_argument(
        "-j",
        "--use-json",
        dest="use_json",
        metavar="json_file",
        help="Create playlist using the json_file passed, instead of a music directory.",
    )

    parser.set_defaults(func=do_stuff)

    args = parser.parse_args()
    args.func(args)
