import streamlit as st
import json
from google import genai
from google.genai import types

client = genai.Client()

def execute_player_trade(current_player: str, new_player: str, logic: str) -> str:
    st.success(f"TRADE EXECUTED: Swapped {current_player} for {new_player}")
    st.info(f"AGENT LOGIC: {logic}")
    return "Trade processed successfully."

st.title("🤖 Autonomous Fantasy Manager")

# Load the mock live data
with open('live_match_state.json', 'r') as f:
    match_data = json.load(f)
    
st.write("### Live Match Feed", match_data)

if st.button("Run Manager Analysis"):
    with st.spinner("Agent is reasoning..."):
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="You are an autonomous fantasy cricket manager...",
                tools=[execute_player_trade], 
                temperature=0.2,
            )
        )
        response = chat.send_message(str(match_data))
        st.write("### Agent Conclusion")
        st.write(response.text)