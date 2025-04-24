# gemini_functions.py
import google.generativeai as genai
import streamlit as st
from typing import Optional, Tuple

class GeminiManager:
    def __init__(self):
        """Initialize Gemini manager."""
        self.model = None
        self.api_key_configured = False
    
    def configure_api_key(self, api_key: str) -> Tuple[bool, str]:
        """Configure the Gemini API key."""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.api_key_configured = True
            return True, "API Key configured successfully!"
        except Exception as e:
            self.api_key_configured = False
            return False, f"Error configuring API key: {str(e)}"
    
    def generate_response(self, prompt: str) -> Tuple[Optional[object], Optional[str]]:
        """Get streaming response from Gemini model."""
        if not self.api_key_configured or not self.model:
            return None, "API key not configured"
        
        try:
            response = self.model.generate_content(
                prompt,
                stream=True
            )
            return response, None
        except Exception as e:
            return None, f"Error generating response: {str(e)}"
    
    def display_streaming_response(self, response_generator) -> str:
        """Display streaming response with typing indicator."""
        full_response = ""
        message_placeholder = st.empty()
        
        try:
            for chunk in response_generator:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
        except Exception as e:
            st.error(f"Error in streaming response: {str(e)}")
            return full_response
        
        message_placeholder.markdown(full_response)
        return full_response