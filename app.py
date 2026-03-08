import streamlit as st
from ui import home, revenue_page, payroll_page, opex_page, financing_page, review_page, insights_page, modeler_page, optimizer_page
from config.version import PLATFORM_VERSION, BUILD_DATE


st.set_page_config(
    page_title="Operating Model",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """
    Global session state initialization (WPP-SESSION-INIT-001).
    Ensures core session state variables are initialized before page routing.
    """
    defaults = {
        "revenue_streams": [],
        "payroll_roles": [],
        "opex_categories": [],
        "financing_sources": [],
        "model_inputs": {},
        "forecast_periods": 36,
        "purchase_price": 0.0,
        "scenario_name": "Business Scenario"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Initialize session state before page routing
initialize_session_state()

st.sidebar.title("Operating Model")

pages = {
    "🏠 Home": home,
    "💵 Revenue": revenue_page,
    "👥 Payroll": payroll_page,
    "📋 Operating Expenses": opex_page,
    "🏦 Financing": financing_page,
    "📊 Review": review_page,
    "💡 Insights": insights_page,
    "🎯 Modeler": modeler_page,
    "🎯 Deal Optimizer": optimizer_page
}

selection = st.sidebar.radio("Go to", list(pages.keys()))

st.sidebar.divider()

periods = st.session_state.get('periods', 36)
time_mode = st.session_state.get('time_mode', 'monthly')
forecast_years = periods // 12 if time_mode == 'monthly' else periods

st.sidebar.markdown("""
### Model Info
- **Platform Version:** {version}
- **Build Date:** {build_date}
- **Time Mode:** {mode}
- **Forecast Length:** {years} Years
- **Periods:** {periods}
- **Revenue Streams:** {rev_count}
- **Payroll Roles:** {payroll_count}
- **Opex Items:** {opex_count}
""".format(
    version=PLATFORM_VERSION,
    build_date=BUILD_DATE,
    mode=time_mode.capitalize(),
    years=forecast_years,
    periods=periods,
    rev_count=len(st.session_state.get('revenue_streams', [])),
    payroll_count=len(st.session_state.get('payroll_roles', [])),
    opex_count=len(st.session_state.get('opex_items', []))
))

page = pages[selection]
page.render()

# Sidebar footer with version
st.sidebar.divider()
st.sidebar.markdown(f"<div style='text-align: center; color: #888; font-size: 0.85em;'>FinanceModeler v{PLATFORM_VERSION}</div>", unsafe_allow_html=True)
