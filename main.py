"""
Create a spotify playlist based on the mp3 files in a directory.
"""

import argparse
import os
from pathlib import Path
from mltk.spotiply import *
from mltk.genres import clean_tags, scrape_genres
from uuid import uuid4

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(THIS_DIR, "data/")


def do_stuff(args):

    # create data dir if doesnt exist 
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    if args.credentials:
        generate_credentials_json()
    
    elif args.clean_genres:
        clean_tags(args.clean_genres)   

    elif args.clean_genres2:
        clean_tags(args.clean_genres2, use_artist_genre=True)

    elif args.update_genres:
        scrape_genres()

    elif args.liked_songs or args.liked_songs_urls:
        json_file = os.path.join(DATA_DIR, "liked_songs.json")
        get_liked_songs(spotify_connect(), json_file, urls=args.liked_songs_urls)

    elif args.create_playlist or args.use_json:
        playlist_name = uuid4().hex if args.playlist_name else args.playlist_name
        json_file = os.path.join(DATA_DIR, playlist_name + ".json")
        sp = spotify_connect()

        if args.use_json:
            playlist_name = Path(args.use_json).stem
            create_spotify_playlist(sp, playlist_name, args.use_json)
        else:
            music_dir_to_json(args.create_playlist, json_file)
            get_spotify_track_id(sp, json_file)
            if not args.disable_playlist:
                create_spotify_playlist(sp, playlist_name, json_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="spotiply",
        description="Create a spotify playlist based on the mp3 files in a directory.",
    )
    # group1 = parser.add_mutually_exclusive_group(required=False)

    group1 = parser.add_mutually_exclusive_group(required=True)
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
        "-c",
        "--credentials",
        dest="credentials",
        action="store_true",
        help="Generate credentials.json file",
    )
    group1.add_argument(
        "-ls",
        "--liked-songs",
        dest="liked_songs",
        action="store_true",
        help="Generate json of your liked songs.",
    )
    group1.add_argument(
        "--liked-songs-urls",
        dest="liked_songs_urls",
        action="store_true",
        help="Generate txt file of the urls of your liked songs.",
    )
    group1.add_argument(
        "-g",
        dest="clean_genres",
        metavar="MUSIC_DIR",
        help="Clean the genres and other tag information for the mp3 files in MUSIC_DIR.",
    )
    group1.add_argument(
        "-ga",
        dest="clean_genres2",
        metavar="MUSIC_DIR",
        help="Clean the genres and other tag information (using artist to determine the genre) for the mp3 files in MUSIC_DIR.",
    )
    group1.add_argument(
        "-ug",
        dest="update_genres",
        action="store_true",
        help="Updates the genre mapping json.",
    )

    group2 = parser.add_argument_group("To be used with --create-playlist")
    group2.add_argument(
        "-dp",
        "--disable-playlist",
        dest="disable_playlist",
        action="store_true",
        help="Will disable creating the actual spotify playlist.",
    )
    group2.add_argument(
        "-p",
        "--playlist-name",
        dest="playlist_name",
        type=str,
        help="Name of the playlist you want to create. If not provided will use a uuid.",
    )
    parser.set_defaults(func=do_stuff)

    args = parser.parse_args()
    args.func(args)
