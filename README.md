# Spotiply🎧

Allows you to create a spotify playlist based on the mp3 files in a directory.

## Usage:


```bash
python spotiply [-h] [-c | -dp | -j json_file] [music_dir] [playlist_name]
```

| positional arguments |                                                                           |
| -------------------- | ------------------------------------------------------------------------- |
| music_dir            | Full path of the music directory.                                         |
| playlist_name        | Name of the playlist you want to create. If not provided will use a uuid. |

| options                     |                                                                             |
| --------------------------- | --------------------------------------------------------------------------- |
| -h, --help                  | Show this help message and exit.                                            |
| -c, --credentials           | Generate credentials.json file.                                             |
| -dp, --disable-playlist     | Do all tasks, except creating the actual spotify playlist.                  |
| -j , --use-json `json_file` | Create playlist using the `json_file` passed, instead of a music directory. |