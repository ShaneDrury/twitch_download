#!/usr/bin/env python3
# encoding: utf-8
"""
twitch_download -- small commandline tool to download Past Broadcasts from Twitch.

downloads and converts Broadcasts from Twitch


@author:     Florian Trabauer

@copyright:  2014 Florian Trabauer. All rights reserved.

@license:    GPLv2

@contact:    florian@trabauer.com
@deffield    updated: 2014-08-11
                initial version
            2014-08-18:
                div. Code reorgansisiert
                Fehler behoben. Es gibt PastBroadcasts ohne meta_game.
                Diese werden als no_meta_game deklariert
            2014-08-19:
                Statt einer Json Struktur wird ein VideoInfo Objekt erzeugt das die relevanten Informationen aus der
                 Justin.tv API enthält. So können auch andere APIs implementiert werden, die auch nur ein VideoInfo
                 Objekt erzeugen.

            2014-11-03:
                Twitch API changed. This script uses know api.twitch.tv instead of api.justin.tv

            2014-11-04:
                The script works now on OS X (Apple)
                Fixed Config Initialization Error

            2014-11-09:
                Small improvements and some bugfixes

"""
from optparse import OptionParser
import os
import configparser

from lib.twitch import TwitchApiError
from lib.twitch import get_video_info
from lib.twitch_download import download_broadcast
from lib.twitch_download import safe_filename


def print_help():
    print("In this interactive mode you can enter the Stream id or the URL to the past broadcast")
    print("Append the quality after the specication of the stream.\n"
          "The best quality available will be selected by default.\n"
          "Examples:\n"
          "\thttp://www.twitch.tv/esltv_sc2/b/585041281 720p\n"
          "\thttp://www.twitch.tv/esltv_sc2/b/585041281\n"
          "\t585041281\n"
          "\t585041281 240p\n"
          "\n"
          "Available qualities: "
          "240p, 360p, 480p, 720p, source\n")
    print("This script will create the folder hierarchy <yourLibrary\<game>\<streamer> for your download.")
    print("After the download the script converts the Past Broadcast in a mp4-Video with ffmpeg")


def interactive_mode(download_folder):
    print('twitch_download\n===============\n\nYou can enter StreamId\'s, help or exit')

    os.chdir(download_folder)

    while True:
        interactive_input = input('> ')

        try:
            if interactive_input == 'exit':
                exit(0)
            elif interactive_input == 'help':
                print_help()
                continue
            else:
                interactive_input = interactive_input.split()
                broadcast_info = get_video_info(interactive_input[0])

        except TwitchApiError as e:
            print('TwitchApiError occured: ', e.message)
            continue
        if broadcast_info.meta_game is None:  # Es gibnt Broadcasts ohne meta_game angabe
            # Ersetze None durch 'no_meta_game' um einen Fehler im filename zu vermeiden.
            broadcast_info.meta_game = 'no_meta_game'
        filename = os.path.join(
            download_folder,
            safe_filename(
                os.path.join(
                    broadcast_info.meta_game,
                    broadcast_info.channel_name,
                    broadcast_info.title + '_' + broadcast_info.start_time
                )
            )
        )
        if len(interactive_input) == 2:
            filename = filename + interactive_input[1]
            download_broadcast(broadcast_info, filename, interactive_input[1])
        elif len(interactive_input) == 1:
            download_broadcast(broadcast_info, filename)
        else:
            print("invalid input! Specify URL, StreamID with optional Quality\n")
            print_help()


if __name__ == "__main__":

    # create cfg-file if needed.
    config = configparser.RawConfigParser()
    download_folder = ''
    ffmpeg_bin = ''
    if not os.path.exists('twitch_download.cfg'):
        print('config_file not found!')
        while len(download_folder) == 0:
            download_folder = input('specify download folder: ')
            if not os.path.exists(download_folder):
                print('invalid download directory!')
                download_folder = ''
        while len(ffmpeg_bin) == 0:
            ffmpeg_bin = input('specifiy the \"ffmpeg\" - binary (Full PATH): ')
            if not os.path.exists(ffmpeg_bin):
                print('ffmpeg not found!')
                ffmpeg_bin = ''
        config.set('DEFAULT', 'download_folder', download_folder)
        config.set('DEFAULT', 'ffmpeg_bin', ffmpeg_bin)
        with open('twitch_download.cfg', 'w') as configfile:
            config.write(configfile)
    else:
        config.read('twitch_download.cfg')
        try:
            download_folder = config.get('DEFAULT', 'download_folder')
            ffmpeg_bin = config.get('DEFAULT', 'ffmpeg_bin')
        except (KeyError, configparser.NoOptionError) as ex:
            print('Invalid  config-file:\n\n' + str(
                ex) + '\n\nFix the twitch_download.cfg or delete it to generate a new one.')
            exit()
    usage = "usage: %prog [TwitchBroadcastId ... ]"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) == 0:
        interactive_mode(download_folder)
    else:
        broadcastURLs = args
        for broadcastURL in broadcastURLs:
            try:
                video_info = get_video_info(broadcastURL)
            except TwitchApiError as ex:
                print('TwitchApiError occurred', ex.message)
                continue
            f = os.path.join(download_folder, safe_filename(
                os.path.join(
                    video_info.meta_game, video_info.channel_name,
                    video_info.title, video_info.start_time)
                )
            )
            download_broadcast(video_info, f, ffmpeg_bin)
