import csv

import os
import eyed3
import json
import requests
import time
import logging
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from .spotiply import spotify_connect
from fuzzywuzzy import process

URL = "https://www.chosic.com/list-of-music-genres/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
}


def scrape_genres(path):
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

    # dump to json file
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(genre_dict, fp, indent=2)

    return genre_dict


def clean_genres(path):
    with open(path, "r", encoding="utf-8") as fp:
        genre_dict = json.load(fp)

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
            genre_dict[k] = "hardstyle"
        elif "dance" in k.lower() and v.strip().lower() == "electronic":
            genre_dict[k] = "dance"

    # some additions
    genre_dict["top 40"] = "pop"
    genre_dict["club"] = "club"

    # dump to json file
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(genre_dict, fp, indent=2)

    return genre_dict


def clean_tag(audio, debug=False):
    audio = eyed3.load(audio)

    # update year
    if not debug:
        if audio.tag.original_release_date:
            audio.tag.recording_date = audio.tag.original_release_date

    # update genre
    if audio.tag.genre:
        genre = audio.tag.genre.name

        update_to = map_genre(genre)
        update_to = "hip-hop" if update_to == "hip hop" else update_to
        
        if debug:
            print("\n" + Path(audio.path).name)
            print(genre, "->", update_to)
        else:
            #  copy original genre to comments
            if not debug and audio.tag.comments.get("genre") is None:
                audio.tag.comments.set(f"{genre}", "genre")

            # actually update the genre tag
            if update_to:
                audio.tag.genre = update_to

            # save tag
            try:
                audio.tag.save(preserve_file_time=True)
            except:
                print("Issue saving tag...skipping: ", audio.path)


def clean_tags(path, debug=False):
    logging.getLogger("eyed3").setLevel(logging.ERROR)

    paths = [x for x in Path(path).rglob("*.mp3")]
    if not debug:
        paths = tqdm(paths)
    
    for audio in paths:
        clean_tag(audio, debug)


def get_spotify_genres_from_song_archive(
    archive="/home/nickneos/Downloads/zspotify/ZSpotify Music/.song_archive",
    csv_file="artist_genres.csv",
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
        print("Reading .song_archive....")

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


def map_genre(genre, genres_json="/home/nickneos/projects/spotiply/genres.json"):
    with open(genres_json, "r", encoding="utf-8") as fp:
        genre_dict = json.load(fp)
    
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


def most_frequent(list):
    if len(list) > 0:
        return max(set(list), key = list.count)
    else:
        return None    

