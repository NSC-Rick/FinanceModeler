import streamlit as st
import json
from datetime import datetime
from engine.validation import (
    get_default_model_inputs,
    validate_scenario_json,
    session_state_to_model_inputs,
    model_inputs_to_session_state
)
from config.version import PLATFORM_VERSION, BUILD_DATE

# Check if openpyxl is available for Excel export
try:
    import openpyxl
    from utils.exporters import export_scenario_to_excel
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    export_scenario_to_excel = None


def initialize_session_state():
    """Initialize session state with default values."""
    if 'time_mode' not in st.session_state:
        st.session_state.time_mode = 'monthly'
    
    if 'periods' not in st.session_state:
        st.session_state.periods = 36  # Default: 3 years × 12 months
    
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
    
    # Legacy single loan (preserved for backward compatibility and Basic mode)
    if 'loan_principal' not in st.session_state:
        st.session_state.loan_principal = 50000.0
    
    if 'loan_annual_rate' not in st.session_state:
        st.session_state.loan_annual_rate = 0.06
    
    if 'loan_term_months' not in st.session_state:
        st.session_state.loan_term_months = 60
    
    if 'loan_start_period' not in st.session_state:
        st.session_state.loan_start_period = 0
    
    # Dual loan structure (Advanced mode only)
    if 'business_loan_amount' not in st.session_state:
        st.session_state.business_loan_amount = 0.0
    
    if 'business_interest_rate' not in st.session_state:
        st.session_state.business_interest_rate = 0.06
    
    if 'business_amort_years' not in st.session_state:
        st.session_state.business_amort_years = 5
    
    if 'real_estate_loan_amount' not in st.session_state:
        st.session_state.real_estate_loan_amount = 0.0
    
    if 'real_estate_interest_rate' not in st.session_state:
        st.session_state.real_estate_interest_rate = 0.06
    
    if 'real_estate_amort_years' not in st.session_state:
        st.session_state.real_estate_amort_years = 10
    
    # Backward compatibility migration: map legacy loan_principal to business_loan_amount
    if st.session_state.loan_principal > 0 and st.session_state.business_loan_amount == 0.0:
        st.session_state.business_loan_amount = st.session_state.loan_principal
        st.session_state.business_interest_rate = st.session_state.loan_annual_rate
        st.session_state.business_amort_years = st.session_state.loan_term_months / 12
    
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
    
    if 'business_stage' not in st.session_state:
        st.session_state.business_stage = 'acquisition'
    
    if 'model_mode' not in st.session_state:
        st.session_state.model_mode = 'startup'
    
    if 'working_capital_source' not in st.session_state:
        st.session_state.working_capital_source = 'buyer_injected'
    
    if 'starting_ar_balance' not in st.session_state:
        st.session_state.starting_ar_balance = 0.0
    
    if 'starting_ap_balance' not in st.session_state:
        st.session_state.starting_ap_balance = 0.0
    
    if 'starting_inventory_balance' not in st.session_state:
        st.session_state.starting_inventory_balance = 0.0
    
    if 'capital_stack' not in st.session_state:
        st.session_state.capital_stack = {
            'enabled': False,
            'uses': {
                # Legacy field (preserved for backward compatibility)
                'purchase_price': 0.0,
                'closing_costs': 0.0,
                # New Business Acquisition fields
                'business_purchase_price': 0.0,
                'inventory_adjustment': 0.0,
                'business_closing_costs': 0.0,
                # New Real Estate fields
                'real_estate_purchase': 0.0,
                'real_estate_closing_costs': 0.0,
                # Other uses
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
    
    # Backward compatibility migration: convert legacy purchase_price to new structure
    if 'capital_stack' in st.session_state:
        uses = st.session_state.capital_stack.get('uses', {})
        
        # If legacy purchase_price exists and new fields don't exist, migrate
        if 'purchase_price' in uses and uses.get('purchase_price', 0.0) > 0:
            if 'business_purchase_price' not in uses or uses.get('business_purchase_price', 0.0) == 0.0:
                # Migrate legacy purchase_price to business_purchase_price
                st.session_state.capital_stack['uses']['business_purchase_price'] = uses['purchase_price']
                st.session_state.capital_stack['uses']['real_estate_purchase'] = 0.0
        
        # Ensure all new fields exist with defaults
        if 'business_purchase_price' not in uses:
            st.session_state.capital_stack['uses']['business_purchase_price'] = 0.0
        if 'business_closing_costs' not in uses:
            st.session_state.capital_stack['uses']['business_closing_costs'] = 0.0
        if 'real_estate_purchase' not in uses:
            st.session_state.capital_stack['uses']['real_estate_purchase'] = 0.0
        if 'real_estate_closing_costs' not in uses:
            st.session_state.capital_stack['uses']['real_estate_closing_costs'] = 0.0
    
    if 'seasonality' not in st.session_state:
        st.session_state.seasonality = {
            'enabled': False,
            'mode': 'OFF',  # OFF, Retail, Custom
            'custom_weights': [8.33] * 12  # Default to even distribution (100/12)
        }
    
    # Revenue input method variables
    if 'revenue_input_method' not in st.session_state:
        st.session_state.revenue_input_method = 'Monthly Revenue Target'
    
    if 'monthly_revenue' not in st.session_state:
        st.session_state.monthly_revenue = 0.0
    
    if 'avg_sale' not in st.session_state:
        st.session_state.avg_sale = 25.0
    
    if 'monthly_transactions' not in st.session_state:
        st.session_state.monthly_transactions = 0.0
    
    if 'customers_per_day' not in st.session_state:
        st.session_state.customers_per_day = 0.0
    
    if 'days_open' not in st.session_state:
        st.session_state.days_open = 30.0
    
    # Modeler variables (persist during session, NOT saved to JSON)
    if 'modeler_revenue_adj' not in st.session_state:
        st.session_state.modeler_revenue_adj = 0.0
    
    if 'modeler_expense_adj' not in st.session_state:
        st.session_state.modeler_expense_adj = 0.0
    
    if 'modeler_scope' not in st.session_state:
        st.session_state.modeler_scope = "Year 1 Only"


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
    
    1. **Configure Time Mode** below (Monthly = 36 periods ; Annual = 3 years)
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
        
        scenario_name = st.text_input(
            "Scenario Name",
            value="Business Scenario",
            help="Name this scenario before downloading",
            key="scenario_name_input"
        )
        
        # Determine available export formats
        if EXCEL_AVAILABLE:
            export_formats = ["Excel (.xlsx)", "JSON"]
            format_help = "Choose export format: Excel for spreadsheet analysis, JSON for data portability"
        else:
            export_formats = ["JSON"]
            format_help = "Excel export unavailable (openpyxl not installed). JSON export available."
        
        export_format = st.radio(
            "Export Format",
            export_formats,
            horizontal=True,
            help=format_help
        )
        
        # Show warning if Excel not available and user might expect it
        if not EXCEL_AVAILABLE and len(export_formats) == 1:
            st.warning("⚠️ Excel export is unavailable. Install openpyxl to enable Excel (.xlsx) exports.")
        
        model_inputs = session_state_to_model_inputs(st.session_state)
        
        # Add scenario name, platform version, and build date to model inputs for exports
        model_inputs['scenario_name'] = scenario_name
        model_inputs['platform_version'] = PLATFORM_VERSION
        model_inputs['build_date'] = BUILD_DATE
        
        # Sanitize filename: replace spaces with underscores, remove special chars
        safe_name = scenario_name.strip().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in ('_', '-'))
        
        # Add timestamp to filename (YYYYMMDD_HHMM)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Prepare export data based on format
        if export_format == "Excel (.xlsx)" and EXCEL_AVAILABLE:
            # Get DataFrames from session state if available
            income_statement_df = None
            cash_flow_df = None
            dscr_series = None
            revenue_df = None
            kpis_df = None
            
            if hasattr(st.session_state, 'income_statement_df'):
                income_statement_df = st.session_state.income_statement_df
            if hasattr(st.session_state, 'cash_flow_df'):
                cash_flow_df = st.session_state.cash_flow_df
            if hasattr(st.session_state, 'dscr_series'):
                dscr_series = st.session_state.dscr_series
            if hasattr(st.session_state, 'revenue_df'):
                revenue_df = st.session_state.revenue_df
            if hasattr(st.session_state, 'kpis_df'):
                kpis_df = st.session_state.kpis_df
            
            export_data = export_scenario_to_excel(
                model_inputs,
                income_statement_df=income_statement_df,
                cash_flow_df=cash_flow_df,
                dscr_series_or_df=dscr_series,
                revenue_df=revenue_df,
                kpis_df=kpis_df,
                include_raw_json=True
            )
            filename = f"{safe_name}_{timestamp}.xlsx"
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            button_label = "Download Scenario (Excel)"
        else:
            export_data = json.dumps(model_inputs, indent=2)
            filename = f"{safe_name}_{timestamp}.json"
            mime_type = "application/json"
            button_label = "Download Scenario (JSON)"
        
        st.download_button(
            label=button_label,
            data=export_data,
            file_name=filename,
            mime=mime_type,
            help=f"Download current scenario as {export_format}"
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
            "Time Mode",
            options=['monthly', 'annual'],
            index=0 if st.session_state.time_mode == 'monthly' else 1,
            help="Monthly = 36 periods (3 years), Annual = 3 periods (3 years)"
        )
        
        if time_mode != st.session_state.time_mode:
            st.session_state.time_mode = time_mode
            st.session_state.periods = 36 if time_mode == 'monthly' else 3
            st.rerun()
    
    with col2:
        st.metric(
            label="Forecast Length",
            value=f"3 Years ({st.session_state.periods} periods)",
            help=f"{'3 years × 12 months' if st.session_state.time_mode == 'monthly' else '3 years'}"
        )
    
    st.divider()
    
    st.info("👈 Use the sidebar to navigate through the model sections.")
