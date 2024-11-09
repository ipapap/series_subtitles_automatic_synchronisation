import os
import re
import subprocess
import shutil
import argparse
import sync

def find_season_and_episode(folder_path, subtitle_folder, force_redo=False, allow_multiple=False):
    # Define the regular expression to match the pattern s00e00
    pattern = re.compile(r's(\d{2})e(\d{2})', re.IGNORECASE)

    # Lists to store results for video files and subtitles
    video_results = []
    subtitle_results = []

    # Walk through the folder and get all files for video
    for root, _, files in os.walk(folder_path):
        for file in files:
            try:
                # Search for the pattern in the filename
                match = pattern.search(file)
                if match:
                    season = match.group(1)
                    episode = match.group(2)
                    if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                        video_results.append({'file': file, 'season': season, 'episode': episode, 'root': root})
            except UnicodeDecodeError as e:
                print(f"Skipping file due to Unicode error: {file}, error: {e}")

    # Walk through the subtitles folder and get all subtitle files
    for root, _, files in os.walk(subtitle_folder):
        for file in files:
            try:
                # Search for the pattern in the filename
                match = pattern.search(file)
                if match:
                    season = match.group(1)
                    episode = match.group(2)
                    if file.lower().endswith(('.srt', '.sub', '.vtt')):
                        subtitle_results.append({'file': file, 'season': season, 'episode': episode, 'root': root})
            except UnicodeDecodeError as e:
                print(f"Skipping file due to Unicode error: {file}, error: {e}")

    # Print results for video files
    if video_results:
        print("Video Files:")
        for result in video_results:
            print(f"File: {result['file']}, Season: {result['season']}, Episode: {result['episode']}")
    else:
        print("No matching video files found.")

    # Print results for subtitle files
    if subtitle_results:
        print("\nSubtitle Files:")
        for result in subtitle_results:
            print(f"File: {result['file']}, Season: {result['season']}, Episode: {result['episode']}")
    else:
        print("No matching subtitle files found.")

    # Synchronize subtitles with video files and rename subtitles
    for video in video_results:
        matching_subs = [sub for sub in subtitle_results if sub['season'] == video['season'] and sub['episode'] == video['episode']]
        if matching_subs:
            # Sync all matching subtitles
            video_path = os.path.join(video['root'], video['file'])
            for idx, sub in enumerate(matching_subs):
                sub_path = os.path.join(sub['root'], sub['file'])
                new_sub_name = os.path.splitext(video['file'])[0] + (f"_{idx:02d}" if idx > 0 else "") + os.path.splitext(sub['file'])[1]
                new_sub_path = os.path.join(video['root'], new_sub_name)

                # Skip if the new subtitle name already exists unless force_redo is True
                if os.path.exists(new_sub_path) and not force_redo:
                    print(f"Subtitle {new_sub_name} already exists. Skipping... Use force_redo=True to redo.")
                else:
                    # Use ffsubsync to sync the subtitles with the video
                    print(f"Synchronizing subtitles for {video['file']} with {sub['file']}...")
                    try:
                        sync.sync(video_path, sub_path, new_sub_path,encoding='windows-1253') # 'utf-8' in general, 'windows-1253' for greek
                        print(f"Renamed and saved synchronized subtitle as {new_sub_name}")
                    except Exception as e:
                        print(f"Error during synchronization for {video['file']} with {sub['file']}: {e}")

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize subtitles with video files and rename accordingly.")
    parser.add_argument('folder_path', type=str, help="The folder path containing the video files.")
    parser.add_argument('--subtitle_folder', default='subtitles', type=str, help="The folder path containing the subtitle files.")
    parser.add_argument('--force-redo', action='store_true', help="Force redo the synchronization and renaming process.")
    parser.add_argument('--allow-multiple', action='store_false', help="Allow synchronization and renaming of multiple subtitle files per video.")
    args = parser.parse_args()

    find_season_and_episode(args.folder_path, os.path.join(args.folder_path,args.subtitle_folder), args.force_redo, args.allow_multiple)


