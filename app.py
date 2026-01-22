import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import plotly.express as px
from PIL import Image
from dotenv import load_dotenv

# --- 1. PAGE CONFIGURATION ---
# This must be the very first Streamlit command.
try:
    icon_image = Image.open("masterball.png")
    st.set_page_config(
        page_title="PROkedex AI",
        page_icon=icon_image,
        layout="wide"
    )
except FileNotFoundError:
    # Fallback if the image isn't in the folder yet
    st.set_page_config(page_title="PROkedex AI", page_icon="🔮", layout="wide")

# --- 2. THEME & STYLING ---
# Injecting custom CSS for the Masterball aesthetic
st.markdown("""
    <style>
    /* Main background */
    .stApp { background-color: #1a1121; color: white; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { 
        background-color: #2d2036; 
        border-right: 2px solid #7E308E; 
    }
    
    /* User chat bubble (Masterball Pink) */
    [data-testid="stChatMessageUser"] {
        background-color: #F8008A !important;
        border-radius: 15px;
        color: white !important;
    }
    
    /* Assistant chat bubble (Clean Silver/White) */
    [data-testid="stChatMessageAssistant"] {
        background-color: #f0f2f6 !important;
        border-radius: 15px;
        color: #1a1a1a !important;
    }
    
    /* Titles and text */
    h1, h2, h3 { color: #7E308E; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA & AI INITIALIZATION ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("API Key not found. Please set GEMINI_API_KEY in your .env file or Streamlit secrets.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@st.cache_data
def load_data():
    return pd.read_csv('pokemon.csv')

df = load_data()

# --- 4. SIDEBAR LOGIC ---
def show_radar_chart(pokemon_name):
    p_data = df[df['name'] == pokemon_name].iloc[0]
    
    # Stats for the radar chart
    stats = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
    values = [p_data[s] for s in stats]
    
    # 
    fig = px.line_polar(
        r=values,
        theta=['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed'],
        line_close=True,
        color_discrete_sequence=['#F8008A'] # Pink accent line
    )
    fig.update_traces(fill='toself')
    fig.update_layout(
        polar=dict(bgcolor="#2d2036", radialaxis=dict(visible=True, range=[0, 255])),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    st.sidebar.markdown(f"## {pokemon_name}")
    st.sidebar.plotly_chart(fig, use_container_width=True)
    st.sidebar.write(f"**Type:** {p_data['type1']} / {p_data['type2'] if pd.notna(p_data['type2']) else 'None'}")
    st.sidebar.write(f"**Classification:** {p_data['classfication']}")

# --- 5. MAIN CHAT INTERFACE ---
st.title("🛡️ PROkedex AI")
st.write("Analyze battle stats and strategies using professional TCG data.")

# 

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about a Pokémon's stats or weaknesses..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Find if a Pokémon name exists in the prompt
    found_pokemon = next((name for name in df['name'].values if name.lower() in prompt.lower()), None)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            if found_pokemon:
                show_radar_chart(found_pokemon)
                # Inject the row data as context for Gemini
                pokemon_row = df[df['name'] == found_pokemon].to_string()
                full_prompt = f"Use this data for context: {pokemon_row}\n\nUser Question: {prompt}"
            else:
                full_prompt = prompt

            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})