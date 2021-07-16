# Youtube Audio Downloader
import os, re, time, requests, ffmpeg
from moviepy.editor import *
from pytube import *

total_errors = 0
titles = []
replace_type = 0


def clear():
    global total_errors, titles
    total_errors = 0
    titles = []
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def downloader(video, vtype):
    global total_errors, titles, replace_type
    try:
        # Get video and title
        yt = YouTube(video)
        vidtitle = yt.title
        print("\n" + str(len(titles) + 1) + ". Found Video: " + vidtitle)

        # Get file name
        fname = re.sub(yt.author + " ", "", vidtitle)

        if '-' in re.sub("^(?:\w+\s+){3}([^\n\r]+)$", "", fname) and vtype == 'a':
            fname = re.sub('^[^-]*- ', "", fname)

        fname = re.sub('[\\/:"\'*?<>|.,%#$+!`&{}@=]+', "", fname)

        if replace_type == 1:
            fname = re.sub(' ', "_", fname)

        fname = re.sub('\([^)]*\)', "", fname)

        if 'ft' in fname:
            fname = re.sub('ft[^|]*', "", fname)

        if fname[-1] == '_':
            fname = fname[:-1]
        if fname[0] == '_':
            fname = fname[0:]

        fname = fname.strip()
        fname = fname.strip('_')

        print('File name will be: ' + fname)

        titles.append(fname)

        if vtype == 'a':
            # Choose Stream
            chosenDownload = yt.streams.get_audio_only()
            print("Located highest bitrate audio stream for video: '" + vidtitle + "'. Downloading now...")

            # Download Vid
            chosenDownload.download(filename=fname, max_retries=5)
            print("Finished Download, converting to mp3 file")

            # Convert from mp4 to mp3
            video = AudioFileClip(fname + '.mp4')
            video.write_audiofile(fname + '.mp3')
            print("Finished Conversion")
            os.remove(fname + '.mp4')
            print("Removed mp4")
        elif vtype == 'v':
            # Choose Stream
            chosenDownload = yt.streams.get_highest_resolution()
            print("Located highest resolution video stream for video: '" + vidtitle + "'. Downloading now...")

            # Download Vid
            chosenDownload.download(filename=fname, max_retries=5)
            print("Finished Download")
        elif vtype == 'h':
            fname = fname.strip('-')
            # Choose Stream - video
            chosenDownload = yt.streams.filter(only_video=True).first()
            print("Located highest resolution video stream for video: '" + vidtitle + "'. Downloading now...")
            print('Stream is: ' + str(chosenDownload))

            # Download Vid
            chosenDownload.download(filename=fname, max_retries=5)
            print("Finished Download")

            if chosenDownload.mime_type == 'video/webm':
                print("Downloading audio")

                # Choose Stream - audio
                chosenDownload = yt.streams.get_audio_only('webm')
                print("Located highest bitrate audio stream for video: '" + vidtitle + "'. Downloading now...")

                # Download audio
                chosenDownload.download(filename=fname + '1', max_retries=5)
                print("Finished Download, Combining files")

                input_video = ffmpeg.input(fname + '.webm')
                merged_audio = ffmpeg.input(fname + '1.webm')

                # Combine Files
                time.sleep(2)
                (
                    ffmpeg
                    .concat(input_video, merged_audio, v=1, a=1)
                    .output(fname + ".mp4")
                    .run(overwrite_output=True, cmd='ffmpeg.exe')
                )

                # Remove Extras
                os.remove(fname + '.webm')
                os.remove(fname + '1.webm')

        print("Link to thumbnail: \n" + yt.thumbnail_url)
    except:
        print("Error downloading, possible forbidden download")
        total_errors += 1

    print("\n")


def downPlaylist(vtype):
    playlist = Playlist(input("Link to Playlist: \n"))
    listName = playlist.title
    print("Accessing playlist: " + listName)

    listName = re.sub('[\\/:"\'*?<>|.,%#$+!`&{}@=]+', "", listName)

    try:
        os.mkdir(listName)
    except:
        print("Playlist already downloaded (folder already exists). Carrying on...")

    try:
        url = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['thumbnailRenderer']['playlistCustomThumbnailRenderer']['thumbnail']['thumbnails'][2]['url']
    except KeyError:
        try:
            url = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['thumbnailRenderer']['playlistVideoThumbnailRenderer']['thumbnail']['thumbnails'][2]['url']
        except KeyError:
            print("Cant find playlist thumbnail, are you sure you entered a link to a playlist?")
    print('Thumbnail url is:', url)

    get_thumb = (input("Would you like to download the playlist thumbnail?\n") or 'y')

    try:
        if get_thumb[0].lower() == 'y':
            lname = 'thumbnail.png'
            data = requests.get(url)
            with open(lname, 'wb')as file:
                file.write(data.content)

            os.rename(lname, listName + "/" + lname)
            print("Downloaded thumbnail")
    except:
        print("Thumbnail already downloaded")

    print("proceeding to download", str(playlist.length) + " files\n")
    for video in playlist:
        downloader(video, vtype)

    global titles, total_errors
    print("\n"*3 + "Finished Downloading from playlist with a total error count of " + str(total_errors) + ", moving to playlist folder now")

    # Move files
    # Find file ending
    f_end = {
        'a': '.mp3',
        'v': '.mp4',
    }

    for n in titles:
        os.rename(n + f_end[vtype], listName + "/" + n + ".mp3")

    print("Finished")


def main():
    global replace_type

    # Find if user would like to download 1 file or many files using playlist
    dtype = (input("Would you like to download video's through YouTube playlists? [yes for playlist, no for single video, leave empty for spotify download]\n") or 's')

    replace_type_string = 'n'

    if dtype[0].lower() in ['y','n']:
        vidtype = (input("Would you like to download as a video or audio or high res video? [v or a or h]\n") or 'a')
        replace_type_string = (input('Lastly, would you like to replace spaces in the file name with "_" (underscores)?\n') or 'n')

    if replace_type_string[0].lower() == 'y':
        replace_type = 1

    if dtype[0].lower() == 'y':
        downPlaylist(vidtype[0].lower())
    elif dtype[0].lower() == 'n':
        vidurl = input("Enter link to youtube video\nlink: ")
        downloader(vidurl, vidtype[0].lower())
    else:
        link = input("Link: \n")
        try:
            command = ("spotdl " + link + " --ffmpeg ffmpeg.exe")
            os.system('cmd /c "' + command + '"')
            os.remove('.cache')
        except:
            print("Error getting spotify track")
            print("To use this feature you must have spotify downloader installed:\nhttps://github.com/spotDL/spotify-downloader")
            time.sleep(10)


print("====================")
print("    By Rohan S.")
print("====================")
main()

x = 1
while x == 1:
    exit = (input("Type 'y' to exit, or just click enter to repeat...\n") or '  n')

    if exit[0].lower() == 'y':
        x = 0
    else:
        clear()
        time.sleep(1)
        main()
