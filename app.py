import streamlit as st
import pandas as pd
import os
from PIL import Image
from dotenv import load_dotenv
import plotly.express as px

# Try the direct import for the new 2026 SDK
try:
    from google import genai
except ImportError:
    st.error("SDK Load Error: Please ensure 'google-genai' is in your requirements.txt and reboot the app.")

# --- 1. PAGE CONFIG & ICON ---
load_dotenv()
current_dir = os.path.dirname(os.path.abspath(__file__))

# Case-sensitive check for Linux
icon_filename = "masterball-icon.png" 
icon_path = os.path.join(current_dir, icon_filename)

try:
    icon_image = Image.open(icon_path)
    st.set_page_config(
        page_title="PROkedex AI",
        page_icon=icon_image,
        layout="centered", # Keeps it to the middle 1/3
        initial_sidebar_state="collapsed"
    )
except Exception:
    st.set_page_config(page_title="PROkedex AI", page_icon="🔮", layout="centered")

# --- 2. MASTERBALL THEME ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    .stApp { background-color: #1a1121; color: white; }
    [data-testid="stChatMessageUser"] { background-color: #F8008A !important; border-radius: 15px; }
    [data-testid="stChatMessageAssistant"] { background-color: #f0f2f6 !important; border-radius: 15px; color: #1a1a1a !important; }
    .m-title { text-align: center; color: #7E308E; font-size: 2.5rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='m-title'>🛡️ PROkedex AI</h1>", unsafe_allow_html=True)

# --- 3. AI CLIENT SETUP ---
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@st.cache_data
def load_data():
    return pd.read_csv('pokemon.csv')

df = load_data()

# --- 4. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about a Pokémon..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    found = next((n for n in df['name'].values if n.lower() in prompt.lower()), None)

    with st.chat_message("assistant"):
        if found:
            p = df[df['name'] == found].iloc[0]
            
            # Radar Chart
            stats_keys = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
            fig = px.line_polar(
                r=[p[k] for k in stats_keys],
                theta=['HP', 'Atk', 'Def', 'Sp.Atk', 'Sp.Def', 'Speed'],
                line_close=True, color_discrete_sequence=['#F8008A']
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", polar=dict(bgcolor="rgba(0,0,0,0)"), font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            
            context = f"Analyze these stats for {found}: {p.to_dict()}. Question: {prompt}"
        else:
            context = prompt

        try:
            # Using the stable 2.0/2.5 model ID for early 2026
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=context
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"AI Error: {str(e)}")