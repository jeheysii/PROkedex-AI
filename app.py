import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from PIL import Image
from dotenv import load_dotenv
import plotly.express as px

# --- 1. PAGE CONFIG & ICON FIX ---
load_dotenv()

# We use a more robust way to find the file
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "masterball-icon.png")

try:
    icon_image = Image.open(icon_path)
    st.set_page_config(
        page_title="PROkedex AI",
        page_icon=icon_image,
        layout="centered",
        initial_sidebar_state="collapsed"
    )
except Exception:
    # Fallback to emoji if file is missing or corrupted
    st.set_page_config(page_title="PROkedex AI", page_icon="🔮", layout="centered")

# --- 2. MASTERBALL THEME & CENTERED UI ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    .block-container { max-width: 800px; padding-top: 2rem; }
    .stApp { background-color: #1a1121; color: white; }
    
    /* Masterball Pink for User */
    [data-testid="stChatMessageUser"] { 
        background-color: #F8008A !important; 
        border-radius: 20px 20px 5px 20px; 
    }
    /* Clean Silver for AI */
    [data-testid="stChatMessageAssistant"] { 
        background-color: #f0f2f6 !important; 
        border-radius: 20px 20px 20px 5px; 
        color: #1a1a1a !important; 
    }
    .m-title { text-align: center; color: #7E308E; font-size: 2.5rem; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='m-title'>🛡️ PROkedex AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.7;'>Gemini 2.5 Battle Intelligence</p>", unsafe_allow_html=True)

# --- 3. STABLE AI SETUP ---
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# STABLE MODEL NAMES for 2026:
# Use 'gemini-1.5-flash' for maximum stability if 2.0/2.5 errors out.
# For now, let's try the latest recognized stable version.
try:
    model = genai.GenerativeModel('gemini-1.5-flash') 
except:
    model = genai.GenerativeModel('gemini-pro')

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
    # 1. Show User Message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Search for Pokémon
    found = next((n for n in df['name'].values if n.lower() in prompt.lower()), None)

    with st.chat_message("assistant"):
        response_text = ""
        
        if found:
            p = df[df['name'] == found].iloc[0]
            
            # --- VISUALIZATION ---
            stats_keys = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
            fig = px.line_polar(
                r=[p[k] for k in stats_keys],
                theta=['HP', 'Atk', 'Def', 'Sp.Atk', 'Sp.Def', 'Speed'],
                line_close=True, color_discrete_sequence=['#F8008A']
            )
            fig.update_traces(fill='toself')
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="white", polar=dict(bgcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # --- AI INTERPRETATION ---
            # We explicitly ask the AI to provide a textual analysis
            full_prompt = f"""
            You are a Pokémon Battle Expert. Use the following data to answer the user's request.
            Include a detailed interpretation of their stats and a battle recommendation.
            
            DATA: {p.to_dict()}
            USER QUESTION: {prompt}
            """
        else:
            full_prompt = prompt

        try:
            with st.spinner("Professor is thinking..."):
                response = model.generate_content(full_prompt)
                response_text = response.text
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            st.error(f"AI error: {e}")