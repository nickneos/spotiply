import csv
import eyed3
import json
import logging
import os
import spotipy
import time
from pathlib import Path, PurePosixPath
from spotipy import util
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm
from urllib.parse import unquote, urlparse

# my modules
from .utils import clean_artist, clean_song_title

# constants
CREDENTIALS = "credentials.json"
SPOTIFY_TRACK_URL = "https://open.spotify.com/track/"

# initialise logging
logger = logging.getLogger(__name__)


def music_dir_to_json(path, out_file):
    logger.info(f"Exporting songs to {out_file}")
    songs = []
    for file in sorted(os.listdir(path)):
        if file.endswith(".mp3"):
            mp3 = os.path.join(path, file)
            audio = eyed3.load(mp3)

            song = {"artist": audio.tag.artist, "title": audio.tag.title}
            songs.append(song)

    with open(out_file, "w", encoding="utf-8", newline="") as f:
        json.dump(songs, f, indent=4)

    return songs


def rbox_to_json(txt_file, out_file):
    logger.info(f"Exporting reckordbox txt file to {out_file}")
    songs = []

    with open(txt_file, "r", encoding="utf-16", newline="") as f:
        dr = csv.DictReader(f, delimiter="\t")
        for row in dr:
            song = {"artist": row["Artist"].split(", ")[0], "title": row["Track Title"]}
            songs.append(song)

    with open(out_file, "w", encoding="utf-8", newline="") as f:
        json.dump(songs, f, indent=4)

    return songs


def get_spotify_track_id(sp, json_file):
    # read song names from json file
    with open(json_file, "r", encoding="utf-8") as f:
        songs = json.load(f)

    # loop over song names and search for them on spotify
    logger.info(f"Songs in {json_file} to be searched on spotify")
    for song in tqdm(songs):
        result = search_spotify_song(sp, song["artist"], song["title"])

        if result:
            song["spotify"] = {
                "id": result["id"],
                "artist": result["artist"],
                "title": result["title"],
                "url": result["url"],
            }
        else:
            log_not_found(
                f"{song['artist']} - {song['title']}",
                Path(json_file).parent.joinpath(
                    Path(json_file).stem + "-not_found.txt"
                ),
            )

    # update json file with spotify details
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=4)
        logger.info(f"Updated {json_file} with spotify details")

    return songs


def search_spotify_song(sp, artist, title):
    try:
        artist = clean_artist(artist)
        title = clean_song_title(title)
    except KeyError:
        return None

    # build query search string
    query = f"{title} artist:{artist}"
    # query = urllib.parse.quote(query, safe=":")

    try:
        # we'll assume first result is correct and save its id
        results = sp.search(q=query, limit=1, type="track")
        result = results["tracks"]["items"][0]
        logger.debug(result)
    except IndexError:
        return None

    try:
        return {
            "id": result["id"],
            "artist": result["artists"][0]["name"],
            "title": result["name"],
            "url": SPOTIFY_TRACK_URL + result["id"],
        }
    except Exception as e:
        logger.error(f"{type(e).__name__} - {e}")
        return None


def create_spotify_playlist(sp, playlist_name, json_file):
    # read song names from json file
    with open(json_file, "r", encoding="utf-8") as f:
        songs = json.load(f)

    # generate list of song_ids
    song_ids = []
    n_songs = 0
    n_songs_spotify = 0
    for song in songs:
        n_songs += 1
        if "spotify" in song:
            n_songs_spotify += 1
            if song["spotify"]["id"] not in song_ids:
                song_ids.append(song["spotify"]["id"])
    logger.info(f"no of songs {n_songs}")
    logger.info(f"no of song_id's {n_songs_spotify}")
    logger.info(f"no of unique song_id's {len(song_ids)}")

    # create a playlist for current user with provided name
    user_id = sp.me()["id"]
    sp.user_playlist_create(user_id, playlist_name, public=False)

    # find playlist's ID
    # there may be multiple playlists with the given name, collect them to a list of tuples (name, id)
    playlists = [
        (x["name"], x["id"])
        for x in sp.current_user_playlists()["items"]
        if x["name"] == playlist_name
    ]

    # add found songs to playlist
    logger.info("Adding songs to playlist...")
    playlist_id = playlists[0][1]  # get the first playlist matching the name
    batch_size = 10
    for i in tqdm(range(0, len(song_ids), batch_size)):
        batch = song_ids[i : i + batch_size]
        time.sleep(1)
        sp.playlist_add_items(playlist_id, batch)


def log_not_found(song, file):
    with open(file, "a", encoding="utf-8") as f:
        f.write(song + "\n")


def spotify_connect():
    """
    Connect to spotify.
    Register app to get tokens first at: https://developer.spotify.com/dashboard/
    """

    if not os.path.exists(CREDENTIALS):
        generate_credentials_json()

    with open(CREDENTIALS, "r", encoding="utf-8") as f:
        credentials = json.load(f)

    client_id = credentials["client_id"]
    client_secret = credentials["client_secret"]
    redirect_uri = credentials["redirect_uri"]
    scope = "playlist-read-private playlist-modify-private user-library-read"
    # change to appropriate scope if playlist is public
    # more about scopes: https://developer.spotify.com/documentation/general/guides/scopes/

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
        )
    )


def generate_credentials_json():
    print("\n")
    print("To connect to spotify we require some tokens")
    print("Register app to get tokens first at: https://developer.spotify.com/dashboard/")

    while True:
        resp = input("\nHas this been done? (y/n) ")
        if resp.lower().strip() == "y":
            break

    credentials = {}
    credentials["client_id"] = input("\nClient ID: ")
    credentials["client_secret"] = input("Client Secret: ")
    credentials["redirect_uri"] = "http://localhost:8080"

    with open(CREDENTIALS, "w", encoding="utf-8") as f:
        json.dump(credentials, f, indent=2)

    print("\nSaved to", CREDENTIALS)


def get_liked_songs(sp, csv_out="data/liked_songs.csv"):
    # get the songs
    batch_size = 50  # 50 is the most spotify will return at a time
    counter = 0

    with open(csv_out, "w", encoding="utf-8") as f:
        csv_writer = csv.writer(f, delimiter="\t")
        csv_writer.writerow(["Num", "Title", "Artists", "TrackID", "URL"])

    if sp:
        for i in range(0, 10000000, batch_size):
            response = sp.current_user_saved_tracks(offset=i, limit=batch_size)
            if len(response["items"]) == 0:
                break

            for item in response["items"]:
                counter += 1
                add_track_data_to_csv(item, counter, csv_out)
        logger.info(f"Generated liked songs file: {csv_out}")


def get_playlist_items(sp, url, csv_out=None):
    batch_size = 50  # 50 is the most spotify will return at a time
    counter = 0

    if not csv_out:
        try:
            csv_out = (
                "data/" + PurePosixPath(unquote(urlparse(url).path)).parts[2] + ".csv"
            )
        except:
            csv_out = "data/playlist.csv"

    with open(csv_out, "w", encoding="utf-8") as f:
        csv_writer = csv.writer(f, delimiter="\t")
        csv_writer.writerow(["Num", "Title", "Artists", "TrackID", "URL"])

    if sp:
        for i in range(0, 10000000, batch_size):
            response = sp.playlist_items(url, offset=i, limit=batch_size)
            if len(response["items"]) == 0:
                break

            for item in response["items"]:
                counter += 1
                add_track_data_to_csv(item, counter, csv_out)


def add_track_data_to_csv(item, track_num, csv_file):
    track_id = "" if not item["track"]["id"] else item["track"]["id"]

    track_info = [
        track_num,
        item["track"]["name"],
        ", ".join([a["name"] for a in item["track"]["artists"]]),
        track_id,
        SPOTIFY_TRACK_URL + track_id,
    ]

    with open(csv_file, "a", encoding="utf-8") as f:
        csv_writer = csv.writer(f, delimiter="\t")
        csv_writer.writerow(track_info)
