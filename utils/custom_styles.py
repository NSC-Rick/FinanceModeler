"""
Custom CSS styles for improved readability.
Enhancement 3 - WPP Financial Modeler v1.1
"""
import streamlit as st


def apply_custom_styles():
    """
    Apply custom CSS styles to improve readability throughout the application.
    
    Enhancement 3: Improves text contrast in blue information panels by setting
    text color to white (#FFFFFF) for better readability.
    """
    st.markdown("""
        <style>
        /* Enhancement 3: Improve guidance text contrast on blue info panels */
        .stAlert[data-baseweb="notification"] div[data-testid="stMarkdownContainer"] p,
        .stAlert[data-baseweb="notification"] div[data-testid="stMarkdownContainer"] li,
        .stAlert[data-baseweb="notification"] div[data-testid="stMarkdownContainer"] strong,
        .stAlert[data-baseweb="notification"] div[data-testid="stMarkdownContainer"] em,
        div[data-testid="stNotificationContentInfo"] p,
        div[data-testid="stNotificationContentInfo"] li,
        div[data-testid="stNotificationContentInfo"] strong,
        div[data-testid="stNotificationContentInfo"] em,
        div[data-testid="stNotificationContentInfo"] div {
            color: #FFFFFF !important;
        }
        
        /* Ensure info panel backgrounds remain blue */
        div[data-testid="stNotificationContentInfo"] {
            background-color: #0E4C92 !important;
        }
        
        /* Also improve contrast for markdown in info panels */
        .stAlert[data-baseweb="notification"][kind="info"] {
            background-color: #0E4C92 !important;
        }
        
        .stAlert[data-baseweb="notification"][kind="info"] * {
            color: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)
