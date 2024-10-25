import numpy as np
from pydub import AudioSegment
import tempfile
from google.cloud import texttospeech
import streamlit as st
import os

def create_silence(duration_ms):
    """Create a silent audio segment of specified duration"""
    return AudioSegment.silent(duration=duration_ms)

def text_to_speech_basic(text, client):
    """Convert a single piece of text to speech without SSML"""
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-D",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        
    )
    
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    # Create a temporary file for the audio segment
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    with open(temp_file.name, "wb") as out:
        out.write(response.audio_content)
    
    # Load the audio segment using pydub
    audio_segment = AudioSegment.from_mp3(temp_file.name)
    
    # Clean up the temporary file
    os.unlink(temp_file.name)
    
    return audio_segment

def convert_text_to_speech(cleaned_text, transcript_data):
    """Convert text to speech with appropriate pauses"""
    client = texttospeech.TextToSpeechClient()
    
    # Split text into segments based on [PAUSE] markers
    segments = cleaned_text.split('[PAUSE]')
    segments = [seg.strip() for seg in segments if seg.strip()]
    
    # Calculate total original duration
    total_original_duration = transcript_data['word_timings'][-1]['end_time']
    
    # Initialize combined audio
    combined_audio = AudioSegment.empty()
    
    # Process each segment
    # Initialize a progress bar
    progress_bar = st.progress(0)

    for i, segment in enumerate(segments):
        if segment:
            # Convert segment to speech
            audio_segment = text_to_speech_basic(segment, client)
            combined_audio += audio_segment
            
            # Add pause after segment (except for the last segment)
            if i < len(segments) - 1:
                # Calculate pause duration
                pause_duration = 1000  # 1 second in milliseconds
                if i < len(transcript_data['word_timings']) - 1:
                    current_pos = sum(len(s.split()) for s in segments[:i+1])
                    if current_pos < len(transcript_data['word_timings']) - 1:
                        pause_duration = int(
                            (transcript_data['word_timings'][current_pos + 1]['start_time'] - 
                            transcript_data['word_timings'][current_pos]['end_time']) * 1000
                        )
                        pause_duration = max(pause_duration, 1000)  # Minimum 1 second pause
                
                silence = create_silence(pause_duration)
                combined_audio += silence
        
        # Update progress bar
        progress_bar.progress((i + 1) / len(segments))

    
    # Add final pause to match original duration if needed
    current_duration = len(combined_audio) / 1000  # Convert to seconds
    if current_duration < total_original_duration:
        remaining_duration = int((total_original_duration - current_duration) * 1000)
        final_silence = create_silence(remaining_duration)
        combined_audio += final_silence
    
    # Export the final audio
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    combined_audio.export(output_file.name, format="mp3")
    st.success("Audio content written to file")
    
    return output_file.name