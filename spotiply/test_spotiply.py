import core as spotiply


def test_clean_song_title():
    assert spotiply.clean_song_title("this is A TEST!!!! (remix)") == "this is a test"
    assert spotiply.clean_song_title("this is A TEST!!!! (remix) [remix] (2)") == "this is a test"


def test_clean_artist():
    assert spotiply.clean_artist("Kanye feat Jay-Z") == "kanye"
    assert spotiply.clean_artist("Jay-Z & Kanye") == "jayz"
