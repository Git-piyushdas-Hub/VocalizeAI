import streamlit as st
import os
import requests

def clean_transcription_with_gpt4(transcript_data):
    azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if azure_openai_key and azure_openai_endpoint:
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": azure_openai_key
            }
            
            # Modified prompt to maintain sentence structure and add more strategic pauses
            data = {
                "messages": [{
                    "role": "user",
                    "content": f"""Please clean up the following transcription, following these rules:
                    1. Remove grammatical mistakes and filler words
                    2. Add [PAUSE] in these situations:
                    - After every 3 words
                    - Between complete thoughts or sentences
                    - After important points
                    - After every comma
                    - Where natural breaks in speech would occur
                    3. Keep the text natural and conversational
                    4. Maintain proper punctuation
                    
                    Original text:
                    {transcript_data['full_text']}"""
                }],
                "max_tokens": 1000
            }
            
            response = requests.post(azure_openai_endpoint, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                cleaned_text = result["choices"][0]["message"]["content"].strip()
                return cleaned_text
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            st.error(f"Failed to connect to GPT-4: {str(e)}")
            return None
    else:
        st.warning("Azure OpenAI API key or endpoint is missing.")
        return None