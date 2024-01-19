import eyed3
import os
import re


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


if __name__ == "__main__":
    path = "/home/nickneos/Music/Collections/Neos' Old School Urban Collection/"
    # rename_mp3_in_dir(path, debug=True)
    rename_mp3_in_dir(path)
