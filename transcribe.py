import io
from google.cloud import speech_v1p1beta1 as speech

def transcribe_audio(audio_file):
    client = speech.SpeechClient()
    
    with io.open(audio_file, 'rb') as audio_file:
        content = audio_file.read()
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=44100,
        language_code="en-US",
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True  # Enable word timing information
    )
    
    audio = speech.RecognitionAudio(content=content)
    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=90)
    
    # Store both transcript and timing information
    transcript_data = {
        'full_text': '',
        'word_timings': []
    }
    
    for result in response.results:
        alternative = result.alternatives[0]
        transcript_data['full_text'] += alternative.transcript
        
        # Store word timing information
        for word in alternative.words:
            transcript_data['word_timings'].append({
                'word': word.word,
                'start_time': word.start_time.total_seconds(),
                'end_time': word.end_time.total_seconds()
            })
    
    return transcript_data