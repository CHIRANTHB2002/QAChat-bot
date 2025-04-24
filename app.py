import streamlit as st
from dotenv import load_dotenv
from typing import Optional, Tuple, List, Dict

from supabase_functions import SupabaseManager
from gemini_functions import GeminiManager

# Load environment variables
load_dotenv()

def initialize_session_state() -> None:
    """Initialize session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'gemini_manager' not in st.session_state:
        st.session_state.gemini_manager = GeminiManager()
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None
    if 'supabase_manager' not in st.session_state:
        st.session_state.supabase_manager = SupabaseManager()
    if 'conversations' not in st.session_state:
        st.session_state.conversations = []
    if 'needs_name_update' not in st.session_state:
        st.session_state.needs_name_update = False

def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Gemini AI Chat",
        page_icon="🤖",
        layout="wide"
    )

def apply_custom_css() -> None:
    """Apply custom CSS for chat interface."""
    st.markdown("""
        <style>
        .stChat {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 10px;
            margin: 10px 0;
        }
        .user-message {
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
        }
        .assistant-message {
            background-color: #f0f4c3;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
        }
        .conversation-item {
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            cursor: pointer;
        }
        .conversation-item:hover {
            background-color: #f0f2f6;
        }
        .active-conversation {
            background-color: #e3f2fd;
        }
        </style>
    """, unsafe_allow_html=True)

def clear_chat_history() -> None:
    """Clear the chat history."""
    st.session_state.chat_history = []

def display_chat_message(role: str, content: str) -> None:
    """Display a chat message in the UI."""
    with st.chat_message(role):
        st.markdown(content)

def add_message_to_history(role: str, content: str) -> None:
    """Add a message to the chat history."""
    st.session_state.chat_history.append({"role": role, "content": content})
    if st.session_state.current_conversation_id:
        save_conversation()

def handle_user_input(prompt: str) -> None:
    """Handle user input and generate response."""
    if not st.session_state.gemini_manager.api_key_configured:
        st.error("Please enter your Gemini API key in the sidebar first.")
        return
    
    # Create new conversation if none exists
    if st.session_state.current_conversation_id is None:
        create_new_conversation()
    
    # Update conversation name if this is the first message
    if st.session_state.needs_name_update and prompt:
        new_name = st.session_state.supabase_manager.generate_conversation_name(prompt)
        st.session_state.supabase_manager.update_conversation_name(
            st.session_state.current_conversation_id, 
            new_name
        )
        st.session_state.needs_name_update = False
        load_conversations()
    
    # Add user message to history and display
    add_message_to_history("user", prompt)
    display_chat_message("user", prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        response, error = st.session_state.gemini_manager.generate_response(prompt)
        
        if error:
            st.error(error)
            add_message_to_history("assistant", error)
        else:
            full_response = st.session_state.gemini_manager.display_streaming_response(response)
            add_message_to_history("assistant", full_response)

def create_new_conversation(first_message: str = None) -> None:
    """Create a new conversation."""
    db = st.session_state.supabase_manager
    
    # Initially create with a generic name
    name = db.generate_conversation_name()
    
    result = db.create_conversation(name)
    if result:
        st.session_state.current_conversation_id = result['id']
        st.session_state.chat_history = []
        st.session_state.needs_name_update = True
        load_conversations()

def load_conversations() -> None:
    """Load all conversations."""
    st.session_state.conversations = st.session_state.supabase_manager.load_conversations()

def load_conversation(conversation_id: str) -> None:
    """Load a specific conversation."""
    result = st.session_state.supabase_manager.load_conversation(conversation_id)
    if result:
        st.session_state.current_conversation_id = conversation_id
        st.session_state.chat_history = result['chat_history']

def save_conversation() -> None:
    """Save current conversation."""
    if st.session_state.current_conversation_id:
        st.session_state.supabase_manager.update_conversation(
            st.session_state.current_conversation_id,
            st.session_state.chat_history
        )

def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation."""
    if st.session_state.supabase_manager.delete_conversation(conversation_id):
        if st.session_state.current_conversation_id == conversation_id:
            st.session_state.current_conversation_id = None
            st.session_state.chat_history = []
        load_conversations()

def render_sidebar() -> None:
    """Render the sidebar with conversations."""
    with st.sidebar:
        st.title("💬 Conversations")
        
        # New conversation button
        if st.button("➕ New Conversation", key="new_conversation"):
            create_new_conversation()
            st.rerun()
        
        st.markdown("---")
        
        # Display conversations
        for conv in st.session_state.conversations:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if st.button(conv['name'], key=f"conv_{conv['id']}", use_container_width=True):
                    load_conversation(conv['id'])
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    delete_conversation(conv['id'])
                    st.rerun()
        
        st.markdown("---")
        
        # API Key configuration
        if not st.session_state.gemini_manager.api_key_configured:
            st.title("⚙️ Configuration")
            
            st.markdown("""
            ### Getting Started
            1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. Enter it below
            3. Start chatting!
            """)
            
            api_key = st.text_input("Enter Gemini API Key", type="password", key="api_key_input")
            
            if api_key:
                success, message = st.session_state.gemini_manager.configure_api_key(api_key)
                if success:
                    st.success(message)
                else:
                    st.error(message)

def render_chat_interface() -> None:
    """Render the main chat interface."""
    # Header with title and clear button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("🤖 Gemini AI Chat Assistant")
    
    with col2:
        if st.session_state.gemini_manager.api_key_configured and st.session_state.chat_history:
            if st.button("🗑️ Clear", key="clear_chat"):
                clear_chat_history()
                st.rerun()
    
    st.markdown("Ask me anything! I'll respond using Google's Gemini AI.")
    
    # Add a separator
    st.markdown("---")
    
    # Display chat history
    for message in st.session_state.chat_history:
        display_chat_message(message["role"], message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        handle_user_input(prompt)

def main() -> None:
    """Main application function."""
    configure_page()
    apply_custom_css()
    initialize_session_state()
    load_conversations()
    
    # Sidebar with conversations
    render_sidebar()
    
    # Main chat interface
    render_chat_interface()
    

if __name__ == "__main__":
    main()