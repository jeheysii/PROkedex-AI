import streamlit as st
import pandas as pd
from google import genai  
from google.genai import types
import os
from PIL import Image
from dotenv import load_dotenv
import plotly.express as px

# --- 1. PAGE CONFIG & ICON ---
load_dotenv()
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "masterball-icon.png")

try:
    icon_image = Image.open(icon_path)
    st.set_page_config(page_title="PROkedex AI", page_icon=icon_image, layout="centered")
except Exception:
    st.set_page_config(page_title="PROkedex AI", page_icon="🔮", layout="centered")

# --- 3. 2026 SDK CLIENT SETUP ---
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
# The Client handles authentication automatically if GEMINI_API_KEY is in secrets
client = genai.Client(api_key=api_key)

@st.cache_data
def load_data():
    return pd.read_csv('pokemon.csv')

df = load_data()

# --- 4. CHAT SYSTEM ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Analyze a Pokémon..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    found = next((n for n in df['name'].values if n.lower() in prompt.lower()), None)

    with st.chat_message("assistant"):
        if found:
            p = df[df['name'] == found].iloc[0]
            
            # Stat Visualization
            stats_keys = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
            fig = px.line_polar(
                r=[p[k] for k in stats_keys],
                theta=['HP', 'Atk', 'Def', 'Sp.Atk', 'Sp.Def', 'Speed'],
                line_close=True, color_discrete_sequence=['#F8008A']
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", polar=dict(bgcolor="rgba(0,0,0,0)"), font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            
            # AI Context
            context_prompt = f"Analyze these stats for {found}: {p.to_dict()}. Question: {prompt}"
        else:
            context_prompt = prompt

        try:
            with st.spinner("Analyzing..."):
                # Updated Model call for 2026
                response = client.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=context_prompt
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"AI Error: {str(e)}")