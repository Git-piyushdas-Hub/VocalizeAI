import PIL.Image
import streamlit as st
import tempfile
import os
import moviepy.editor as mp
import PIL
from dotenv import load_dotenv
from utils import load_video, extract_audio
from transcribe import transcribe_audio
from azure_gpt import clean_transcription_with_gpt4
from synthesis import convert_text_to_speech

credential_path = './<file_name>.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

# Load environment variables
load_dotenv()

# Initialize session state for timing parameters
if 'pause_scale' not in st.session_state:
    st.session_state.pause_scale = 1.5
if 'min_pause' not in st.session_state:
    st.session_state.min_pause = 1.0

# Streamlit App title
st.title('Video Audio Replacement App')

# Sidebar controls for timing adjustment
with st.sidebar:
    st.header("Timing Controls")
    pause_scale = st.slider(
        "Pause Duration Scale",
        min_value=1.0,
        max_value=3.0,
        value=st.session_state.pause_scale,
        step=0.1,
        help="Multiplier for pause durations. Higher values create longer pauses."
    )
    min_pause = st.slider(
        "Minimum Pause Duration (seconds)",
        min_value=0.5,
        max_value=2.0,
        value=st.session_state.min_pause,
        step=0.1,
        help="Minimum duration for any pause"
    )

# Upload the video file
uploaded_file = st.file_uploader("Upload a video file", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    # Create progress container
    progress_container = st.empty()
    
    # Create temporary file and load video
    with progress_container.container():
        st.write("Loading video...")
        tfile_video = tempfile.NamedTemporaryFile(delete=False)
        tfile_video.write(uploaded_file.read())
    
    # Load the video and display
    video = load_video(tfile_video.name)
    st.video(tfile_video.name)
    st.write(f"Video duration: {video.duration} seconds")
    st.write('Video uploaded successfully')
    
    # Extract audio from the video
    with progress_container.container():
        st.write("Extracting audio...")
        tfile_audio = extract_audio(video)
    st.audio(tfile_audio.name)
    
    # Transcribe the audio
    with progress_container.container():
        st.write("Transcribing audio...")
        transcript_data = transcribe_audio(tfile_audio.name)
    
    # Display original transcription with timing info
    st.subheader("Original Transcription")
    st.write(transcript_data['full_text'])
    
    # Show word timing information in an expander
    with st.expander("Show Word Timing Details"):
        for word_timing in transcript_data['word_timings']:
            st.write(f"{word_timing['word']}: {word_timing['start_time']:.2f}s - {word_timing['end_time']:.2f}s")
    
    # Clean the transcription using GPT-4 (Azure)
    with progress_container.container():
        st.write("Cleaning the transcription with GPT-4...")
        cleaned_transcript = clean_transcription_with_gpt4(transcript_data)
    
    if cleaned_transcript:
        st.subheader("Cleaned Transcription")
        st.write(cleaned_transcript)
        
        # Convert text to speech with progress indicator
        with progress_container.container():
            st.write("Converting clean text to speech...")
            # Update session state with current values
            st.session_state.pause_scale = pause_scale
            st.session_state.min_pause = min_pause
            
            # Pass timing parameters to the synthesis function
            cleaned_audio_file = convert_text_to_speech(
                cleaned_transcript, 
                transcript_data
            )
        
        # Play the newly generated audio
        st.subheader("Generated Audio")
        st.audio(cleaned_audio_file)
        
        # Syncing the newly generated audio file with the original video
        with progress_container.container():
            st.write('Syncing the new audio with original video')
            
            try:
                # Load the original video file using moviepy
                video_clip = mp.VideoFileClip(tfile_video.name)
                
                # Load the new synthesized audio file using moviepy
                new_audio_clip = mp.AudioFileClip(cleaned_audio_file)

                # get the original height and width of the video
                original_width, original_height = video_clip.size

                # Get audio duration
                new_audio_duration = new_audio_clip.duration
                st.write(f"New audio duration: {new_audio_duration:.2f} seconds")
                
                # Show duration comparison
                st.write("Duration Comparison:")
                st.write(f"Original video: {video.duration:.2f} seconds")
                st.write(f"New audio: {new_audio_duration:.2f} seconds")
                
                # Set the new audio to the video
                final_video_clip = video_clip.set_audio(new_audio_clip)

                # Resizing the new video to the original video
                final_video_clip = final_video_clip.resize((original_width, original_height), PIL.Image.Resampling.LANCZOS)

                
                # Create a temp file to store the final video file
                final_output_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                
                # Write the final output video with progress bar
                with st.spinner('Rendering final video...'):
                    final_video_clip.write_videofile(
                        final_output_video.name,
                        codec="libx264",
                        audio_codec="aac",
                        preset="ultrafast",
                        fps=video_clip.fps,
                        threads=4
                    )
                
                # Display the final output video
                st.subheader("Final Video")
                st.video(final_output_video.name)
                
                # Provide download button for the final video
                with open(final_output_video.name, 'rb') as file:
                    st.download_button(
                        label="Download Final Video",
                        data=file,
                        file_name="final_video.mp4",
                        mime="video/mp4"
                    )
                
            except Exception as e:
                st.error(f"Error during video processing: {str(e)}")
            
            finally:
                # Close and remove temp files
                video_clip.close()
                new_audio_clip.close()
                final_video_clip.close()
                tfile_video.close()
                tfile_audio.close()
                os.unlink(tfile_video.name)
                os.unlink(tfile_audio.name)
                os.unlink(cleaned_audio_file)
                os.unlink(final_output_video.name)