"""Chat history visualization component for Streamlit UI."""
import streamlit as st
from typing import List, Dict, Any
from datetime import datetime

class ChatHistoryComponent:
    """Component for displaying chat/debate history."""
    
    def __init__(self):
        """Initialize chat history component."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the chat history.
        
        Args:
            message: Message data including:
                - role: The speaker (analyst, skeptic, human)
                - content: The message content
                - framework_layer: Which framework layer this relates to
                - timestamp: When the message was sent
                - evidence: Any supporting evidence
        """
        st.session_state.messages.append(message)

    def render(self) -> None:
        """Render the chat history in Streamlit."""
        st.subheader("Debate History")

        # Add filters if needed
        framework_layer = st.selectbox(
            "Filter by Framework Layer",
            ["All", "Business Strategy", "Marketing Strategy", "Content Strategy", "Content Plan", "Content"]
        )

        # Display messages
        for message in st.session_state.messages:
            # Skip if filtered
            if framework_layer != "All" and message.get("framework_layer") != framework_layer:
                continue

            # Display the message
            with st.chat_message(message["role"]):
                # Main message content
                st.write(message["content"])
                
                # If there's evidence, show it in an expander
                if "evidence" in message and message["evidence"]:
                    with st.expander("View Evidence"):
                        st.json(message["evidence"])
                
                # Show metadata in small text
                st.caption(f"{message.get('framework_layer', 'General')} | {message.get('timestamp', 'No time').strftime('%Y-%m-%d %H:%M:%S')}")

        # Optional: Add export functionality
        if st.button("Export Chat History"):
            # Convert chat history to downloadable format
            chat_data = {
                "messages": st.session_state.messages,
                "exported_at": datetime.now().isoformat()
            }
            st.download_button(
                "Download Chat History",
                data=str(chat_data),
                file_name="debate_history.json",
                mime="application/json"
            )

# Example usage in test_full_system.py:
"""
# In the main UI:
chat_history = ChatHistoryComponent()

# When a new message/event occurs:
chat_history.add_message({
    "role": "analyst",
    "content": "Based on the market analysis...",
    "framework_layer": "Business Strategy",
    "timestamp": datetime.now(),
    "evidence": {"market_size": 5000, "growth_rate": 25}
})

# In the UI rendering:
chat_history.render()
"""
