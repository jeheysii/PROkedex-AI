import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import plotly.express as px
from PIL import Image
from dotenv import load_dotenv

# --- 1. PAGE CONFIG & ICON ---
load_dotenv()

try:
    # Ensure masterball-icon.png is in your GitHub root folder
    icon_image = Image.open("./masterball-icon.png")
    st.set_page_config(
        page_title="PROkedex AI",
        page_icon=icon_image,
        layout="centered", # Keeps the content focused in the middle
        initial_sidebar_state="collapsed"
    )
except Exception:
    st.set_page_config(page_title="PROkedex AI", page_icon="🔮", layout="centered")

# --- 2. LAYOUT & MASTERBALL THEME ---
# Create a 1/3 centered view using columns
col1, col2, col3 = st.columns([0.1, 0.8, 0.1]) # Adjust ratios as needed

with col2:
    st.markdown("""
        <style>
        /* Force-hide sidebar */
        [data-testid="stSidebar"] { display: none; }
        
        /* Masterball Palette */
        .stApp { background-color: #1a1121; color: white; }
        
        /* Message Bubbles */
        [data-testid="stChatMessageUser"] { 
            background-color: #F8008A !important; 
            border-radius: 20px 20px 0px 20px; 
        }
        [data-testid="stChatMessageAssistant"] { 
            background-color: #f0f2f6 !important; 
            border-radius: 20px 20px 20px 0px; 
            color: #1a1a1a !important; 
        }
        
        /* Center Title */
        .title-text { text-align: center; color: #7E308E; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("<h1 class='title-text'>🛡️ PROkedex AI 2.5</h1>", unsafe_allow_html=True)
    st.caption("Centered Battle Intelligence | Powered by Gemini 2.0")

    # --- 3. DATA & AI INITIALIZATION ---
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

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

    if prompt := st.chat_input("Analyze a Pokémon or Type..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Find Pokémon in the dataset
        found = next((n for n in df['name'].values if n.lower() in prompt.lower()), None)

        with st.chat_message("assistant"):
            if found:
                p = df[df['name'] == found].iloc[0]
                
                # Create Radar Chart (Masterball Pink Theme)
                stats_keys = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
                fig = px.line_polar(
                    r=[p[k] for k in stats_keys],
                    theta=['HP', 'Atk', 'Def', 'Sp.Atk', 'Sp.Def', 'Speed'],
                    line_close=True,
                    color_discrete_sequence=['#F8008A']
                )
                fig.update_traces(fill='toself')
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", 
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    polar=dict(bgcolor="rgba(0,0,0,0)")
                )
                st.plotly_chart(fig, use_container_width=True)
                
                context = f"Data for {found}: {p.to_dict()}\nUser: {prompt}"
            else:
                context = prompt

            try:
                response = model.generate_content(context)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"AI Connection Error: {str(e)}")
                st.info("Check if your API Key is valid and the model 'gemini-2.0-flash-exp' is available.")