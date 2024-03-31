import csv

import os
import eyed3
import json
import requests
import time
import logging
import unicodedata
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from fuzzywuzzy import process
from .spotiply import spotify_connect
from .utils import clean_artist, clean_song_title, most_frequent

URL = "https://www.chosic.com/list-of-music-genres/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
}
DATA_FOLDER = os.path.abspath("./data")
GENRE_LOG_FILE = os.path.join(DATA_FOLDER, ".genre_log")
GENRES_JSON = os.path.join(DATA_FOLDER, "genres.json")
ARTIST_GENRES_CSV = os.path.join(DATA_FOLDER, "artist_genres.csv")
SONG_ARCHIVE = "/home/nickneos/Downloads/zspotify/ZSpotify Music/.song_archive"

# initialise logging
logger = logging.getLogger(__name__)


def scrape_genres(out_file=GENRES_JSON):
    headers = requests.utils.default_headers()
    headers.update(HEADERS)
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    # scrape genres
    genres = soup.findAll("li", attrs={"class": "genre-term-basic"})
    subgenres = soup.findAll("li", attrs={"class": "capital-letter genre-term"})

    genre_list = [x.text.strip().lower() for x in genres]
    genre_dict = {}
    genre_lvl_1 = ""

    # loop through subgenres and build dict
    for sg in subgenres:
        genre_lvl_2 = sg.find("a").text.strip().lower()
        if genre_lvl_2 in genre_list:
            genre_lvl_1 = genre_lvl_2
        genre_dict[genre_lvl_2] = genre_lvl_1

    # make adjustments
    for k, v in genre_dict.items():
        if "house" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "house"
        if "disco" in k.lower():
            genre_dict[k] = "disco"
        elif "psytrance" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "psytrance"
        elif "trance" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "trance"
        elif "techno" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "techno"
        elif "hardstyle" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "Hardstyle"
        elif "dance" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "dance"
        elif "electro house" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "electro"
        elif "melbourne bounce" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "electro"
        elif "dutch house" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "electro"
        elif "big room" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "electro"
        elif k.lower() == "electro":
            genre_dict[k] = "electro"
        elif k.lower() == "eurodance":
            genre_dict[k] = "house"

    for k, v in genre_dict.items():
        if v.strip().lower() == "hip hop":
            genre_dict[k] = "hip-hop"

    # some additions
    genre_dict["top 40"] = "pop"
    genre_dict["club"] = "club"

    # dump to json file
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(genre_dict, fp, indent=2)

    logger.info(f"Scraped genres to {out_file}")

    return genre_dict


def clean_tag(
    audio,
    debug=False,
    use_artist_genre=False,
    update_year=True,
    update_genre=True,
    clean_accents=True,
):
    audio = eyed3.load(audio)
    tag_changed = False
    
    ### update year
    if not debug and update_year:
        if audio.tag.recording_date != audio.tag.original_release_date:
            audio.tag.recording_date = audio.tag.original_release_date
            tag_changed = True

    ### remove accents
    if not debug and clean_accents:
        try:
            artist_clean = remove_accents(audio.tag.artist)
            if audio.tag.artist != artist_clean:
                audio.tag.artist = artist_clean
                tag_changed = True
        except:
            pass

        try:
            albumartist_clean = remove_accents(audio.tag.album_artist)
            if audio.tag.album_artist != albumartist_clean:
                audio.tag.album_artist = albumartist_clean
                tag_changed = True
        except:
            pass

        try:
            title_clean = remove_accents(audio.tag.title)
            if audio.tag.title != title_clean:
                audio.tag.title = title_clean
                tag_changed = True
        except:
            pass

    ### update genre
    if audio.tag.genre:
        og_genre = audio.tag.genre.name

        # get mapped genre
        if use_artist_genre:
            update_to = map_artist_genre(clean_artist(audio.tag.artist))
        else:
            update_to = map_genre(og_genre)

        # print debug info
        if debug:
            print("\n" + Path(audio.path).name)
            print(og_genre, "->", update_to)

        # update actual genre tag
        elif update_genre and update_to.lower() != og_genre.lower():
            #  copy original genre to comments
            if not debug and audio.tag.comments.get("genre") is None:
                audio.tag.comments.set(f"{og_genre}", "genre")

            # actually update the genre tag
            audio.tag.genre = update_to
            tag_changed = True

    ### save tag
    if tag_changed:
        try:
            audio.tag.save(preserve_file_time=True)
        except:
            logger.warning(f"Issue saving tag...skipping: {audio.path}")
        logger.info(f"Saved tag: {audio}")


def clean_tags(path, debug=False, use_artist_genre=False, log_file=GENRE_LOG_FILE):
    paths = [x for x in Path(path).rglob("*.mp3")]
    if not debug:
        paths = tqdm(paths)

    for audio in paths:
        # update genre tag
        try:
            # before, after =
            clean_tag(audio, debug, use_artist_genre)
        except:
            continue

        # # log genre change
        # if not debug and after:
        #     if after.lower().strip() != before.lower().strip():
        #         with open(log_file, "a", encoding="utf-8") as f:
        #             csv_writer = csv.writer(f, delimiter="\t")
        #             csv_writer.writerow([audio, before, after])


def get_spotify_genres_from_song_archive(
    archive=SONG_ARCHIVE,
    csv_file=ARTIST_GENRES_CSV,
):
    sp = spotify_connect()

    # create csv if doesnt exist
    if not os.path.exists(csv_file):
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write("artist_id|artist|genres\n")

    # get artists already in csv
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="|")
        artists_in_csv = [row[1] for row in reader]

    # open archive
    with open(archive, "r", encoding="utf-8") as f:
        logger.info(f"Reading {archive}")

        for line in tqdm(f.readlines()):
            row = line.split("\t")

            if row[2] not in artists_in_csv:
                song = sp.track(row[0])
                artist_id = song["artists"][0]["id"]
                time.sleep(5)

                a = sp.artist(artist_id)
                values = [artist_id, a["name"], a["genres"]]

                with open(csv_file, "a", encoding="utf-8") as f:
                    writer = csv.writer(f, delimiter="|")
                    writer.writerow(values)

                artists_in_csv.append(a["name"])


def map_genre(genre, genres_json=GENRES_JSON):
    with open(genres_json, "r", encoding="utf-8") as fp:
        genre_dict = json.load(fp)

    if genre:
        # exact match
        if g := genre_dict.get(genre.lower().strip()):
            return g
        # fuzzy match
        else:
            genres = [k for k, _ in genre_dict.items()]
            results = process.extractBests(genre, genres, score_cutoff=87)
            results = [x[0] for x in results]
            results = [genre_dict.get(x.lower().strip()) for x in results]
            return most_frequent(results)


def map_artist_genre(artist, csv_file=ARTIST_GENRES_CSV, debug=False):
    artist_dict = {}

    # load artist genres csv
    with open(csv_file, "r", encoding="utf-8") as f:
        csv_reader = csv.reader(f, delimiter="|")
        for row in csv_reader:
            artist_dict[row[1].strip().lower()] = (
                row[2].strip("][").replace("'", "").split(", ")
            )
    # exact match
    if artist_genres := artist_dict.get(artist.strip().lower()):
        artist_genres = [map_genre(g) for g in artist_genres]
        return most_frequent(artist_genres)
    # fuzzy match
    else:
        all_artists = [k for k, _ in artist_dict.items()]
        results = process.extractOne(artist, all_artists, score_cutoff=91)
        if results:
            if debug:
                print(results)
            return map_artist_genre(results[0])
        else:
            return None


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def print_audio_info(audio):

    print("\n" + audio.path)
    for attr in dir(audio.tag):
        if attr in [
            "recording_date",
            "original_release_date",
            "artist",
            "album_artist",
            "album",
            "title",
            "genre",
            "comments",
        ]:
            try:
                print(str(attr).upper() + ': ' + str(getattr(audio.tag, attr)))
            except:
                pass

