# supabase_functions.py
from supabase import create_client, Client
from datetime import datetime
import streamlit as st
from typing import Optional, List, Dict, Any
import os

class SupabaseManager:
    def __init__(self):
        """Initialize Supabase client."""
        self.client = None
        self.initialize_client()
    
    def initialize_client(self) -> None:
        """Initialize Supabase client with credentials."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.client = create_client(supabase_url, supabase_key)
            except Exception as e:
                st.error(f"Error initializing Supabase: {str(e)}")
        else:
            st.warning("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")
    
    def create_conversation(self, name: str, chat_history: List[Dict] = None) -> Optional[Dict]:
        """Create a new conversation in Supabase."""
        if not self.client:
            return None
        
        try:
            data = {
                'name': name,
                'chat_history': chat_history or [],
                'created_at': datetime.now().isoformat()
            }
            
            result = self.client.table('conversations').insert(data).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            st.error(f"Error creating conversation: {str(e)}")
            return None
    
    def load_conversations(self) -> List[Dict]:
        """Load all conversations from Supabase."""
        if not self.client:
            return []
        
        try:
            result = self.client.table('conversations')\
                .select('*')\
                .order('created_at', desc=True)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            st.error(f"Error loading conversations: {str(e)}")
            return []
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Load a specific conversation from Supabase."""
        if not self.client:
            return None
        
        try:
            result = self.client.table('conversations')\
                .select('*')\
                .eq('id', conversation_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            st.error(f"Error loading conversation: {str(e)}")
            return None
    
    def update_conversation(self, conversation_id: str, chat_history: List[Dict]) -> bool:
        """Update conversation chat history in Supabase."""
        if not self.client:
            return False
        
        try:
            data = {
                'chat_history': chat_history,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.client.table('conversations')\
                .update(data)\
                .eq('id', conversation_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            st.error(f"Error updating conversation: {str(e)}")
            return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from Supabase."""
        if not self.client:
            return False
        
        try:
            result = self.client.table('conversations')\
                .delete()\
                .eq('id', conversation_id)\
                .execute()
            
            return True
        except Exception as e:
            st.error(f"Error deleting conversation: {str(e)}")
            return False
    
    def generate_conversation_name(self, first_message: str = None) -> str:
        """Generate a name for the conversation."""
        if first_message:
            return first_message[:30] + "..." if len(first_message) > 30 else first_message
        else:
            # Count existing conversations to generate a number
            conversations = self.load_conversations()
            count = len(conversations) + 1
            return f"New Chat {count}"
    
    def update_conversation_name(self, conversation_id: str, new_name: str) -> bool:
        """Update the name of a conversation."""
        if not self.client:
            return False
        
        try:
            data = {
                'name': new_name,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.client.table('conversations')\
                .update(data)\
                .eq('id', conversation_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            st.error(f"Error updating conversation name: {str(e)}")
            return False