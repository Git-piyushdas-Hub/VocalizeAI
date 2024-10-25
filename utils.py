from moviepy.editor import VideoFileClip
import tempfile

# Load video from temp file
def load_video(video_path):
    return VideoFileClip(video_path)

# Extract audio from video and save to a temp file
def extract_audio(video):
    audio = video.audio
    tfile_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    audio.write_audiofile(tfile_audio.name)
    return tfile_audio
