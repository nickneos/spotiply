import eyed3
import os
import time
import spotipy
import json
import re
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm
from pathlib import Path

CREDENTIALS = "credentials.json"


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


def clean_song_title(title):
    title = re.sub(r"\([^\)]*\)", "", title)
    title = re.sub(r"\[[^\]]*\]", "", title)
    title = re.sub(r"[^0-9a-zA-Z ]+", "", title.lower())
    return title.strip()


def clean_artist(artist):
    artist = artist.lower().split(" ft ")[0].split(" & ")[0].split(" vs ")[0]
    artist = re.sub(r"[^0-9a-zA-Z ]+", "", artist.lower())
    return artist.strip()


def get_spotify_track_id(json_file):
    # read song names from json file
    with open(json_file, "r", encoding="utf-8") as f:
        songs = json.load(f)

    # connect to spotify
    sp = spotify_connect()

    # loop over song names and search for them on spotify
    print("Searching for songs...")
    for song in tqdm(songs):
        try:
            artist = clean_artist(song["artist"])
            title = clean_song_title(song["title"])
        except KeyError:
            continue

        # build query search string
        query = f"{title} artist:{artist}"
        # query = urllib.parse.quote(query, safe=":")

        try:
            # we'll assume first result is correct and save its id
            results = sp.search(q=query, limit=1, type="track")
            result = results["tracks"]["items"][0]
        except IndexError:
            log_not_found(
                f"{song['artist']} - {song['title']}",
                Path(json_file).parent.joinpath(
                    Path(json_file).stem + "-not_found.txt"
                ),
            )
            continue

        song["spotify"] = {
            "id": result["id"],
            "artist": result["artists"][0]["name"],
            "title": result["name"],
        }

    # read song names from text file
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=4)

    return songs


def create_spotify_playlist(playlist_name, json_file):
    # read song names from json file
    with open(json_file, "r", encoding="utf-8") as f:
        songs = json.load(f)

    sp = spotify_connect()

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

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=credentials["redirect_uri"],
            scope="playlist-read-private playlist-modify-private",  # change to appropriate scope if playlist is public
            # more about scopes:
            # https://developer.spotify.com/documentation/general/guides/scopes/
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


if __name__ == "__main__":
    # path = "/home/nickneos/Music/Collections/Neos' Old School Urban Collection/"
    # path = "/home/nickneos/Music/Collections/90s & early 2000s Dance/Neos' Old School Dance Collection/"
    # playlist_name = "test123"  # str(uuid.uuid4())
    # j_file = playlist_name + ".json"

    # music_dir_to_json(path, j_file)
    # get_spotify_track_id(j_file)
    # create_spotify_playlist(playlist_name, j_file)

    # print(clean_song_title("this is A TEST!!!! (remix)"))
    # print(clean_song_title("this is A TEST!!!! (remix) [remix] (2)"))
    generate_credentials_json()
