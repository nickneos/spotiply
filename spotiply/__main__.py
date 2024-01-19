"""
Create a spotify playlist based on the mp3 files in a directory.
"""

import argparse
import os
from pathlib import Path
from spotiply import music_dir_to_json, get_spotify_track_id, create_spotify_playlist

THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def do_stuff(args):
    playlist_name = args.playlist_name
    json_file = os.path.join(THIS_DIR, "..", "data",  playlist_name + ".json")

    p = Path(json_file).parent
    p.mkdir(parents=True, exist_ok=True)

    music_dir_to_json(args.music_dir, json_file)
    get_spotify_track_id(json_file)
    create_spotify_playlist(playlist_name, json_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='spotiply',
        description='Create a spotify playlist based on the mp3 files in a directory.')
    parser.add_argument('music_dir',
                       type=str,
                       help='Full path of music directory')
    parser.add_argument('playlist_name',
                       type=str,
                       help='Downloads tracks, playlists and albums from the URLs written in the file passed.')

    parser.set_defaults(func=do_stuff)

    args = parser.parse_args()
    args.func(args)
