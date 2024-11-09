import os
import torch
import numpy as np
import matplotlib.pyplot as plt
import pysrt
import ffmpeg
from scipy.optimize import minimize, least_squares
from scipy.spatial.distance import cdist
from sklearn.linear_model import RANSACRegressor
from update_subtitles import create_new_subtitle_file

def extract_audio(movie_file, output_audio_file, duration_limit=None):
    """
    Extract audio from the given movie file using ffmpeg-python.
    """
    try:
        stream = ffmpeg.input(movie_file)
        if duration_limit:
            stream = stream.output(output_audio_file, vn=None, ac=1, ar=16000, t=duration_limit * 60, format='wav')
        else:
            stream = stream.output(output_audio_file, vn=None, ac=1, ar=16000, format='wav')
        ffmpeg.run(stream, overwrite_output=True)
    except ffmpeg.Error as e:
        print(f"Error occurred during audio extraction: {e}")

def detect_speech_with_silero(audio_file):
    """
    Use a pre-trained PyTorch Silero VAD model to detect speech.
    """
    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
    (get_speech_timestamps, _, read_audio, _, _) = utils

    # Load the audio file
    wav = read_audio(audio_file, sampling_rate=16000)
    
    # Detect speech timestamps
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)
    
    return speech_timestamps

def plot_speech_intervals(speech_intervals, movie_length):
    """
    Plot the speech intervals relative to the movie length.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Plot speech intervals
    for interval in speech_intervals:
        start = interval['start'] / 16000.0
        end = interval['end'] / 16000.0
        ax.barh(1, end - start, left=start, color='skyblue', edgecolor='black')
    
    ax.set_xlabel('Time (seconds)')
    ax.set_title('Speech Intervals in Movie')
    ax.set_xlim(0, movie_length)
    ax.set_yticks([])
    ax.set_yticklabels([])
    plt.show()

def get_movie_length(movie_file):
    """
    Get the movie length using ffmpeg-python.
    """
    try:
        probe = ffmpeg.probe(movie_file)
        duration = float(probe['format']['duration'])
        return duration
    except ffmpeg.Error as e:
        print(f"Error occurred while getting movie length: {e}")
        return None

def get_speech(movie_file, duration_limit=None):
    # Extract audio from the movie
    audio_file = 'temp_audio.wav'
    extract_audio(movie_file, audio_file, duration_limit=duration_limit)

    # Detect speech intervals using Silero VAD model
    speech_intervals = detect_speech_with_silero(audio_file)
    detected_speech = np.asarray([(interval['start'] / 16000.0 + interval['end'] / 16000.0) / 2 for interval in speech_intervals])

    # Get movie length using ffmpeg-python
    movie_length = get_movie_length(movie_file)
    if movie_length is None:
        print("Unable to proceed without knowing the movie length.")
        if os.path.exists(audio_file):
            os.remove(audio_file)
        return

    # If duration limit is specified, use it instead of full movie length
    if duration_limit:
        movie_length = min(movie_length, duration_limit * 60)

    # Print out the speech intervals
    for interval in speech_intervals:
        start = interval['start'] / 16000.0
        end = interval['end'] / 16000.0
        # print(f"Speech from {start:.2f}s to {end:.2f}s")

    # Plot the speech intervals relative to the movie length
    # plot_speech_intervals(speech_intervals, movie_length)

    # Clean up temporary audio file
    if os.path.exists(audio_file):
        os.remove(audio_file)
    return detected_speech

def load_subtitles(subtitle_file):
    """
    Load subtitles from a .srt file and extract timestamps.
    """
    subs = pysrt.open(subtitle_file)
    subtitle_intervals = []
    for sub in subs:
        start_seconds = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000.0
        end_seconds = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000.0
        subtitle_intervals.append({'start': start_seconds, 'end': end_seconds})
        
    return subtitle_intervals

def get_subtitle_speech_intervals(subtitle_file, duration_limit=None):
    """
    Extract subtitle intervals where there is speech.
    """
    subs = pysrt.open(subtitle_file)
    speech_intervals = []
    for sub in subs:
        start_seconds = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000.0
        end_seconds = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000.0
        if duration_limit is None or start_seconds <= duration_limit * 60:
            speech_intervals.append({'start': start_seconds, 'end': end_seconds})
        if duration_limit is not None and end_seconds > duration_limit * 60:
            break

    detected_speech = np.asarray([(interval['start'] + interval['end']) / 2 for interval in speech_intervals])
    return detected_speech

def match_speech_points(audio_speech, sub_speech):
    """
    Match each audio_speech point with the closest point in sub_speech.
    """
    if len(audio_speech) == 0 or len(sub_speech) == 0:
        return np.array([]), np.array([])
    
    distances = cdist(audio_speech.reshape(-1, 1), sub_speech.reshape(-1, 1), metric='euclidean')
    min_indices = np.argmin(distances, axis=1)
    matched_audio = audio_speech
    matched_sub = sub_speech[min_indices]
    return matched_audio, matched_sub

def ransac_alignment(audio_speech, sub_speech):
    """
    Use RANSAC to robustly estimate the linear transformation (shift and scale) between audio speech and subtitle speech.
    """
    if len(audio_speech) == 0 or len(sub_speech) == 0:
        print("Error: One of the input sequences is empty, cannot perform RANSAC alignment.")
        return None, None

    # Match speech points to ensure equal lengths
    matched_audio, matched_sub = match_speech_points(audio_speech, sub_speech)
    if len(matched_audio) == 0 or len(matched_sub) == 0:
        print("Error: Unable to find matching points for RANSAC alignment.")
        return None, None

    # Reshape data for RANSAC model
    X = matched_audio.reshape(-1, 1)
    y = matched_sub.reshape(-1, 1)

    # Use RANSAC regressor to fit a linear model (shift and scale)
    ransac = RANSACRegressor(residual_threshold=10,stop_probability=0.999,min_samples=2)
    ransac.fit(X, y)

    # Extract the estimated scale and shift
    scale_opt = ransac.estimator_.coef_[0][0]
    shift_opt = ransac.estimator_.intercept_[0]

    inlier_count = np.sum(ransac.inlier_mask_)
    print(f"Number of inliers used by RANSAC: {inlier_count}")
    return shift_opt, scale_opt

def sync(movie_filename, sub_filename, out_sub_name,duration_limit_minutes=None):
    audio_speech = get_speech(movie_filename, duration_limit=duration_limit_minutes)
    sub_speech = get_subtitle_speech_intervals(sub_filename, duration_limit=duration_limit_minutes)

    # Use RANSAC to find the optimal shift and scale to minimize the difference between audio and subtitle speech
    shift_opt, scale_opt = ransac_alignment(audio_speech, sub_speech)

    if shift_opt is not None and scale_opt is not None:
        print(f"Optimal shift (RANSAC): {shift_opt}, Optimal scale (RANSAC): {scale_opt}")
        # Create a new subtitle file with the updated timestamps
        create_new_subtitle_file(sub_filename, shift_opt, scale_opt, out_sub_name)
    else:
        print("RANSAC failed to find a valid alignment.")


if __name__ == "__main__":
    movie_filename = "/mnt/sda1/jellyfin/Series/Shogun.2024.S01.1080p.x265-AMBER[EZTVx.to]/Shogun.2024.S01E08.1080p.x265-AMBER[EZTVx.to].mkv"
    sub_filename = "/mnt/sda1/jellyfin/Series/Shogun.2024.S01.1080p.x265-AMBER[EZTVx.to]/Shogun.2024.S01E08.1080p.x265-AMBER[EZTVx.to].srt"
    duration_limit_minutes = 100  # Only analyze the first 10 minutes
    audio_speech = get_speech(movie_filename, duration_limit=duration_limit_minutes)
    sub_speech = get_subtitle_speech_intervals( sub_filename, duration_limit=duration_limit_minutes)

    # Use RANSAC to find the optimal shift and scale to minimize the difference between audio and subtitle speech
    shift_opt, scale_opt = ransac_alignment(audio_speech, sub_speech)

    if shift_opt is not None and scale_opt is not None:
        print(f"Optimal shift (RANSAC): {shift_opt}, Optimal scale (RANSAC): {scale_opt}")
        # Create a new subtitle file with the updated timestamps
        create_new_subtitle_file(sub_filename, shift_opt, scale_opt, "updated_subtitles.srt")
    else:
        print("RANSAC failed to find a valid alignment.")
