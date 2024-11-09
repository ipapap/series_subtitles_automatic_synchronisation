import pysrt

def create_new_subtitle_file(subtitle_file, shift, scale, output_file):
    """
    Create a new subtitle file with updated timestamps based on shift and scale values.
    
    Args:
        subtitle_file (str): Path to the original subtitle file (.srt).
        shift (float): Value to shift subtitle timestamps in seconds.
        scale (float): Value to scale subtitle timestamps.
        output_file (str): Path to save the new subtitle file.
    """
    # Load the original subtitle file
    subs = pysrt.open(subtitle_file)

    # Apply the shift and scale to each subtitle's timestamps
    for sub in subs:
        # Update start time
        start_seconds = (sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000.0)
        new_start_seconds = start_seconds * scale + shift
        sub.start.hours, remainder = divmod(int(new_start_seconds), 3600)
        sub.start.minutes, remainder = divmod(remainder, 60)
        sub.start.seconds = int(remainder)
        sub.start.milliseconds = int((new_start_seconds - int(new_start_seconds)) * 1000)

        # Update end time
        end_seconds = (sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000.0)
        new_end_seconds = end_seconds * scale + shift
        sub.end.hours, remainder = divmod(int(new_end_seconds), 3600)
        sub.end.minutes, remainder = divmod(remainder, 60)
        sub.end.seconds = int(remainder)
        sub.end.milliseconds = int((new_end_seconds - int(new_end_seconds)) * 1000)

    # Save the updated subtitles to the output file
    subs.save(output_file, encoding='utf-8')

if __name__ == "__main__":
    # Example usage
    create_new_subtitle_file('original.srt', shift=5.0, scale=1.05, output_file='updated.srt')
