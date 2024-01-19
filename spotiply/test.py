import spotipy
import re

from my_secrets import *
from spotipy.oauth2 import SpotifyOAuth

def clean_song_title(title):
    title = re.sub(r'\([^\)]*\)', '', title)
    title = re.sub(r'\[[^\]]*\]', '', title)
    title = re.sub(r'[^0-9a-zA-Z ]+', '', title.lower())

    return title.strip()


def clean_artist(artist):
    artist = artist.lower().split(' ft ')[0].split(" & ")[0].split(" vs ")[0]
    artist = re.sub(r'[^0-9a-zA-Z ]+', '', artist.lower())
    return artist.strip()


# connect to spotify
# register app to get tokens first at: https://developer.spotify.com/dashboard/
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="playlist-read-private playlist-modify-private",
    )
)  # change to appropriate scope if playlist is public
# more about scopes: https://developer.spotify.com/documentation/general/guides/scopes/

song = {
        "artist": "112 Ft Jay Z & Lil Kim",
        "title": "Peaches N Cream (Remix)"
    }
artist = clean_artist(song['artist'])
title = clean_song_title(song['title'])

query = f"{title} artist:{artist}"
# query = urllib.parse.quote(query, safe=":")
print(query)
results = sp.search(q=query, limit=1, type="track")
# we'll assume first result is correct and save its id
for result in results["tracks"]["items"]:
    try:
        print("ID: ", result.get("id"))
        print("TITLE: ", result.get("name"))
        print("ARTIST: ", result.get("artists")[0]["name"])
    except:
        pass

