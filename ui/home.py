import streamlit as st
import json
from engine.validation import (
    get_default_model_inputs,
    validate_scenario_json,
    session_state_to_model_inputs,
    model_inputs_to_session_state
)


def initialize_session_state():
    """Initialize session state with default values."""
    if 'time_mode' not in st.session_state:
        st.session_state.time_mode = 'monthly'
    
    if 'periods' not in st.session_state:
        st.session_state.periods = 60
    
    if 'revenue_streams' not in st.session_state:
        st.session_state.revenue_streams = [
            {
                'name': 'Product Sales',
                'price': 100.0,
                'volume': 100.0,
                'growth_rate': 0.10,
                'cogs_override': None
            }
        ]
    
    if 'global_cogs_pct' not in st.session_state:
        st.session_state.global_cogs_pct = 0.30
    
    if 'payroll_roles' not in st.session_state:
        st.session_state.payroll_roles = [
            {
                'role': 'Manager',
                'headcount': 1,
                'pay_type': 'salary',
                'rate': 60000.0,
                'hours_per_week': 40,
                'annual_raise_pct': 0.03,
                'payroll_tax_pct': 0.0765,
                'benefits_pct': 0.15,
                'role_type': 'indirect'
            }
        ]
    else:
        for role in st.session_state.payroll_roles:
            if 'role_type' not in role:
                role['role_type'] = 'indirect'
    
    if 'opex_items' not in st.session_state:
        DEFAULT_OVERHEAD_CATEGORIES = [
            "Rent",
            "Utilities",
            "Heat",
            "Insurance",
            "Maintenance",
            "Subscriptions",
            "Professional Fees",
            "Marketing",
            "Office / Supplies",
            "Miscellaneous"
        ]
        
        st.session_state.opex_items = [
            {
                'name': category,
                'amount': 0.0,
                'growth_rate': 0.03,
                'category': 'fixed'
            }
            for category in DEFAULT_OVERHEAD_CATEGORIES
        ]
    else:
        for item in st.session_state.opex_items:
            if 'category' not in item:
                item['category'] = 'fixed'
    
    if 'loan_principal' not in st.session_state:
        st.session_state.loan_principal = 50000.0
    
    if 'loan_annual_rate' not in st.session_state:
        st.session_state.loan_annual_rate = 0.06
    
    if 'loan_term_months' not in st.session_state:
        st.session_state.loan_term_months = 60
    
    if 'loan_start_period' not in st.session_state:
        st.session_state.loan_start_period = 0
    
    if 'mode' not in st.session_state:
        st.session_state.mode = 'Basic'
    
    if 'ar_days' not in st.session_state:
        st.session_state.ar_days = 0
    
    if 'ap_days' not in st.session_state:
        st.session_state.ap_days = 0
    
    if 'inventory_days' not in st.session_state:
        st.session_state.inventory_days = 0
    
    if 'tax_rate' not in st.session_state:
        st.session_state.tax_rate = 0.25
    
    if 'annual_depreciation' not in st.session_state:
        st.session_state.annual_depreciation = 0.0
    
    if 'owner_compensation' not in st.session_state:
        st.session_state.owner_compensation = {
            'mode': 'distribution',
            'amount': 0.0
        }
    
    if 'capital_stack' not in st.session_state:
        st.session_state.capital_stack = {
            'enabled': False,
            'uses': {
                'purchase_price': 0.0,
                'inventory_adjustment': 0.0,
                'closing_costs': 0.0,
                'working_capital': 0.0,
                'capex': 0.0
            },
            'sources': {
                'buyer_equity': 0.0,
                'community_equity': 0.0,
                'donations': 0.0,
                'bank_loan': {
                    'amount': 0.0,
                    'rate': 0.06,
                    'term': 10
                },
                'seller_note': {
                    'amount': 0.0,
                    'rate': 0.05,
                    'term': 5
                }
            }
        }


def render():
    """Render the home page."""
    initialize_session_state()
    
    st.title("Operating Model")
    st.caption("Structured financial and capital modeling framework")
    
    st.markdown("""
    ### Welcome to Operating Model
    
    This application helps you build SBDC-style financial models with:
    - **Monthly or Annual** time periods
    - **Multiple revenue streams** with growth projections
    - **Role-based payroll** with raises and benefits
    - **Operating expenses** with inflation
    - **Loan amortization** and debt service coverage
    - **Working capital** management (AR/AP/Inventory)
    
    ### Getting Started
    
    1. **Configure Time Mode** below (Monthly = 60 periods, Annual = 5 periods)
    2. Navigate through the sidebar to input your data
    3. Review your financial statements and KPIs
    
    All calculations are transparent and based on your inputs. No values are fabricated.
    """)
    
    st.divider()
    
    st.subheader("Scenario Management")
    
    st.markdown("""
    Save your current model as a JSON file or load a previously saved scenario.
    All inputs will be preserved and can be restored later.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**💾 Save Scenario**")
        model_inputs = session_state_to_model_inputs(st.session_state)
        json_str = json.dumps(model_inputs, indent=2)
        
        st.download_button(
            label="Download Scenario",
            data=json_str,
            file_name="operating_model_scenario.json",
            mime="application/json",
            help="Download current model inputs as JSON file"
        )
    
    with col2:
        st.markdown("**📂 Load Scenario**")
        uploaded_file = st.file_uploader(
            "Upload Scenario",
            type=["json"],
            help="Upload a previously saved scenario JSON file",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            try:
                json_content = uploaded_file.read().decode('utf-8')
                loaded_data = json.loads(json_content)
                
                is_valid, error_msg = validate_scenario_json(loaded_data)
                
                if is_valid:
                    model_inputs_to_session_state(loaded_data, st.session_state)
                    st.success("✅ Scenario loaded successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Invalid scenario file: {error_msg}")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error loading scenario: {str(e)}")
    
    with col3:
        st.markdown("**🔄 Reset Model**")
        if st.button("Reset to Defaults", help="Reset all inputs to default values"):
            defaults = get_default_model_inputs()
            model_inputs_to_session_state(defaults, st.session_state)
            st.success("✅ Model reset to defaults!")
            st.rerun()
    
    st.divider()
    
    st.subheader("Time Mode Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        time_mode = st.radio(
            "Select Time Mode",
            options=['monthly', 'annual'],
            index=0 if st.session_state.time_mode == 'monthly' else 1,
            help="Monthly = 60 periods (5 years), Annual = 5 periods (5 years)"
        )
        
        if time_mode != st.session_state.time_mode:
            st.session_state.time_mode = time_mode
            st.session_state.periods = 60 if time_mode == 'monthly' else 5
            st.rerun()
    
    with col2:
        st.metric(
            label="Total Periods",
            value=st.session_state.periods,
            help=f"{'5 years × 12 months' if st.session_state.time_mode == 'monthly' else '5 years'}"
        )
    
    st.divider()
    
    st.info("👈 Use the sidebar to navigate through the model sections.")
