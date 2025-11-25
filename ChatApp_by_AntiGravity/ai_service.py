import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict

class AIService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Store chat sessions: session_id -> chat_session object
        self.chat_sessions: Dict[str, any] = {}

    async def get_response(self, user_message: str, session_id: str) -> str:
        if not self.model:
            return "I'm sorry, but my brain (API key) is missing. Please check the server configuration."

        try:
            # Get or create chat session
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = self.model.start_chat(history=[])
            
            chat = self.chat_sessions[session_id]
            response = await chat.send_message_async(user_message)
            return response.text
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            return "I'm having trouble thinking right now. Please try again later."

