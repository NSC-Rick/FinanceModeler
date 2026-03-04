import streamlit as st
from ui import home, revenue_page, payroll_page, opex_page, financing_page, review_page, insights_page, modeler_page


st.set_page_config(
    page_title="Operating Model",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("Operating Model")

pages = {
    "🏠 Home": home,
    "💵 Revenue": revenue_page,
    "👥 Payroll": payroll_page,
    "📋 Operating Expenses": opex_page,
    "🏦 Financing": financing_page,
    "📊 Review": review_page,
    "💡 Insights": insights_page,
    "🎯 Modeler": modeler_page
}

selection = st.sidebar.radio("Go to", list(pages.keys()))

st.sidebar.divider()

periods = st.session_state.get('periods', 36)
time_mode = st.session_state.get('time_mode', 'monthly')
forecast_years = periods // 12 if time_mode == 'monthly' else periods

st.sidebar.markdown("""
### Model Info
- **Time Mode:** {mode}
- **Forecast Length:** {years} Years
- **Periods:** {periods}
- **Revenue Streams:** {rev_count}
- **Payroll Roles:** {payroll_count}
- **Opex Items:** {opex_count}
""".format(
    mode=time_mode.capitalize(),
    years=forecast_years,
    periods=periods,
    rev_count=len(st.session_state.get('revenue_streams', [])),
    payroll_count=len(st.session_state.get('payroll_roles', [])),
    opex_count=len(st.session_state.get('opex_items', []))
))

page = pages[selection]
page.render()
