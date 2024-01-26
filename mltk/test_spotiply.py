from spotiply import *


def test_clean_song_title():
    assert clean_song_title("this is A TEST!!!! (remix)") == "this is a test"
    assert clean_song_title("this is A TEST!!!! (remix) [remix] (2)") == "this is a test"


def test_clean_artist():
    assert clean_artist("Kanye feat Jay-Z") == "kanye"
    assert clean_artist("Jay-Z & Kanye") == "jayz"


def test_search_spotify_song():
    assert search_spotify_song(spotify_connect(), "Daft Punk", "One More Time") == {
        "id": "0DiWol3AO6WpXZgp0goxAV",
        "artist": "Daft Punk",
        "title": "One More Time",
    }
    assert search_spotify_song(spotify_connect(), "afadsf", "adfsasdf") is None
