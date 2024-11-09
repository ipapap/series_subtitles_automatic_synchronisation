# Automatic Subtitle Synchronization for Series

This tool automates the synchronization of subtitles for a series by matching video files with their respective subtitle files and aligning timestamps using audio analysis.

## Features

- **Episode & Subtitle Detection**  
  - Scans the specified folder for all available episodes and subtitle files.
  - Automatically pairs subtitle files with corresponding video files.

- **Audio Extraction & Processing**  
  - Extracts audio from each video file.
  - Splits the extracted audio into segments and apply Voice Activity Detection 

- **Timestamp Matching**  
  - Reads the timestamps from the subtitle file.
  - Uses RANSAC (RANdom SAmple Consensus) algorithm to align subtitle timestamps with detected voice activity in the audio.

- **Subtitle Generation**  
  - Creates a new synchronized subtitle file for each episode with the same filename as the video file.

## Folder Structure

Ensure the following folder structure:

- **`parent_folder`**: The main folder containing video files and a `subtitles` folder.
  - **`subtitles/`**: Folder containing subtitle files.
    - **`###s01e01###.srt`**: Subtitle file for episode 1.
    - **`###s01e02###.srt`**: Subtitle file for episode 2.
  - **`###s01e01###.mp4`**: Video file for episode 1.
  - **`###s01e02###.mp4`**: Video file for episode 2.
  
- The naming convention for subtitles and videos should include a common identifier, like `s01e01`, to ensure they are correctly matched by the tool.

- Place all subtitle files inside the `subtitles` folder.
- The naming convention for subtitles and videos should include a common identifier like `01e01` to help the tool match them automatically.

  ## Usage
  python subs4series.py series_folder
