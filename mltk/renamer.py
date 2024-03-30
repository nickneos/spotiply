import eyed3
import os
import re
import unicodedata
from tqdm import tqdm
from pathlib import Path

def rename_mp3_in_dir(path, debug=False):
    for file in sorted(os.listdir(path)):
        if file.endswith(".mp3"):
            mp3 = os.path.join(path, file)
            # print(mp3)
            audio = eyed3.load(mp3)

            # check existence af.tag.artist
            if hasattr(audio, "tag"):
                # check existence af.tag.artist, title
                if all(hasattr(audio.tag, attr) for attr in ["artist", "title"]):
                    # check Empty
                    if audio.tag.artist and audio.tag.title:
                        new_filename = f"{audio.tag.artist} - {audio.tag.title}.mp3"
                        # delete unix chars
                        new_filename = re.sub(
                            r'[\x00\\/\:*"<>\|\\`\'\%\$\^&£]', "", new_filename
                        )
                        print(file, "->", new_filename)

                        if not debug:
                            os.rename(mp3, os.path.join(path, new_filename))

                        continue

            print("Skipping", file)


def remove_accents_from_tags(audio_file):
    audio = eyed3.load(audio_file)

    tag_changed = False

    try:
        artist_clean = remove_accents(audio.tag.artist)
        if audio.tag.artist != artist_clean:
            print(f"\n{audio_file}\n\tARTIST: {audio.tag.artist} -> {artist_clean}")
            audio.tag.artist = artist_clean
            tag_changed = True
    except:
        pass            

    try:
        albumartist_clean = remove_accents(audio.tag.album_artist)
        if audio.tag.album_artist != albumartist_clean:
            print(f"{audio_file}\n\tALBUM ARTIST: {audio.tag.album_artist} -> {albumartist_clean}")
            audio.tag.album_artist = albumartist_clean
            tag_changed = True
    except:
        pass

    try:
        title_clean = remove_accents(audio.tag.title)
        if audio.tag.title != title_clean:
            print(f"{audio_file}\n\tTITLE: {audio.tag.title} -> {title_clean}")
            audio.tag.title = title_clean
            tag_changed = True
    except:
        pass     

    # save tag
    if tag_changed:
        try:
            audio.tag.save(preserve_file_time=True)
        except:
            print("Issue saving tag...skipping: ", audio.path)


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


if __name__ == "__main__":
    # path = "/home/nickneos/Music/Collections/Neos' Old School Urban Collection/"
    # rename_mp3_in_dir(path, debug=True)
    # rename_mp3_in_dir(path)

    path = "/home/nickneos/Music/DJ/tracks/zspotify/electronic"
    files = [fn for fn in Path(path).rglob('*.mp3')]
    for file in tqdm(files):
        remove_accents_from_tags(file)
