import eyed3
import os
import time
import spotipy
import json
import re
from spotipy import util
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm
from pathlib import Path

CREDENTIALS = "credentials.json"
SPOTIFY_TRACK_URL = "https://open.spotify.com/track/"


def music_dir_to_json(path, out_file):
    print("Exporting songs to text file...")
    songs = []
    for file in sorted(os.listdir(path)):
        if file.endswith(".mp3"):
            mp3 = os.path.join(path, file)
            audio = eyed3.load(mp3)

            song = {"artist": audio.tag.artist, "title": audio.tag.title}
            songs.append(song)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=4)

    return songs


def get_spotify_track_id(sp, json_file):
    # read song names from json file
    with open(json_file, "r", encoding="utf-8") as f:
        songs = json.load(f)

    # loop over song names and search for them on spotify
    print("Searching for songs...")
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
    except IndexError:
        return None

    return {
        "id": result["id"],
        "artist": result["artists"][0]["name"],
        "title": result["name"],
        "url": SPOTIFY_TRACK_URL + result["id"],
    }


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
    print("no of songs", n_songs)
    print("no of song_id's", n_songs_spotify)
    print("no of unique song_id's", len(song_ids))

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
    print("Adding songs to playlist...")
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
    print(
        "Register app to get tokens first at: https://developer.spotify.com/dashboard/"
    )

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


def get_liked_songs(sp, json_out, urls=False):
    # get the songs
    results = []
    batch_size = 50  # 50 is the most spotify will return at a time
    counter = 0

    if sp:
        for i in range(0, 10000000, batch_size):
            response = sp.current_user_saved_tracks(offset=i, limit=batch_size)
            if len(response["items"]) == 0:
                break

            for item in response["items"]:
                counter += 1
                track_info = {
                    "id": item["track"]["id"],
                    "artist": item["track"]["artists"][0]["name"],
                    "title": item["track"]["name"],
                    "url": SPOTIFY_TRACK_URL + item["track"]["id"],
                    "track_num": counter,
                    "json_doc": item
                }
                results.append(track_info)

    # dump to json
    with open(json_out, "w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2)

    if urls:
        urls = [track["url"] for track in results]
        filename = os.path.join(Path(json_out).parent, Path(json_out).stem + ".urls")
        with open(filename, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(f"{url}\n")

    return results


def clean_song_title(title):
    if title:
        title = re.sub(r"\([^\)]*\)", "", title)
        title = re.sub(r"\[[^\]]*\]", "", title)
        title = re.sub(r"[^0-9a-zA-Z ]+", "", title.lower())
        return title.strip()
    else:
        return None


def clean_artist(artist):
    if artist:
        artist = (
            artist.lower()
            .split(" ft ")[0]
            .split(" feat ")[0]
            .split(" & ")[0]
            .split(" vs ")[0]
        )
        artist = re.sub(r"[^0-9a-zA-Z ]+", "", artist.lower())
        return artist.strip()
    else:
        return None
