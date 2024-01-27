import re


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


def most_frequent(list):
    if len(list) > 0:
        return max(set(list), key=list.count)
    else:
        return None
