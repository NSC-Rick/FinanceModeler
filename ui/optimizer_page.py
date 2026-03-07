"""
Deal Optimizer Page (WPP-FME-026)

UI for running deal optimization to find optimal capital structures.
"""

import streamlit as st
import pandas as pd
from engine.deal_optimizer import run_deal_optimization


def render():
    """Main render function for the optimizer page."""
    show_optimizer_page()


def show_optimizer_page():
    """Display the deal optimizer page."""
    st.title("🎯 Deal Optimizer")
    
    st.markdown("""
    The Deal Optimizer automatically searches for optimal capital structures that satisfy
    your constraints (DSCR, cash balance) while optimizing for your chosen objective.
    
    **How it works:**
    1. Define your optimization objective (e.g., minimize buyer equity)
    2. Set constraints (minimum DSCR, minimum cash balance)
    3. The optimizer tests thousands of capital structure combinations
    4. Get the best deal structure that meets your requirements
    """)
    
    st.divider()
    
    # Check if model inputs exist
    if 'revenue_streams' not in st.session_state:
        st.warning("⚠️ Please configure your financial model in the Input pages first.")
        return
    
    # Optimization Settings
    st.subheader("⚙️ Optimization Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Optimization Objective")
        
        objective = st.radio(
            "What do you want to optimize?",
            [
                "Minimize Buyer Equity",
                "Maximize Purchase Price",
                "Maximize DSCR",
                "Maximize Owner Income"
            ],
            help="The optimizer will find the best deal structure for this objective"
        )
        
        # Map display to internal value
        objective_mapping = {
            "Minimize Buyer Equity": "minimize_buyer_equity",
            "Maximize Purchase Price": "maximize_purchase_price",
            "Maximize DSCR": "maximize_dscr",
            "Maximize Owner Income": "maximize_owner_income"
        }
        objective_value = objective_mapping[objective]
    
    with col2:
        st.markdown("### 📋 Constraints")
        
        minimum_dscr = st.number_input(
            "Minimum DSCR",
            min_value=0.0,
            max_value=5.0,
            value=1.25,
            step=0.05,
            help="Minimum acceptable Debt Service Coverage Ratio"
        )
        
        minimum_cash_balance = st.number_input(
            "Minimum Cash Balance ($)",
            min_value=0.0,
            max_value=100000.0,
            value=5000.0,
            step=1000.0,
            help="Minimum acceptable cash balance throughout projection"
        )
        
        use_max_loan = st.checkbox("Set Maximum Loan Amount", value=False)
        maximum_loan_amount = None
        if use_max_loan:
            maximum_loan_amount = st.number_input(
                "Maximum Loan Amount ($)",
                min_value=0.0,
                max_value=1000000.0,
                value=300000.0,
                step=10000.0
            )
    
    st.divider()
    
    # Search Ranges
    st.subheader("🔍 Search Ranges")
    
    use_custom_ranges = st.checkbox("⚙️ Customize Search Ranges", value=False)
    
    if use_custom_ranges:
        st.markdown("""
        Define the ranges for each variable the optimizer will search.
        Smaller steps = more thorough search but slower.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Buyer Equity Range**")
            buyer_equity_min = st.number_input("Min ($)", value=0.0, step=5000.0, key="be_min")
            buyer_equity_max = st.number_input("Max ($)", value=150000.0, step=5000.0, key="be_max")
            buyer_equity_step = st.number_input("Step ($)", value=5000.0, step=1000.0, key="be_step")
        
        with col2:
            st.markdown("**Seller Note Range**")
            seller_note_min = st.number_input("Min ($)", value=0.0, step=5000.0, key="sn_min")
            seller_note_max = st.number_input("Max ($)", value=200000.0, step=5000.0, key="sn_max")
            seller_note_step = st.number_input("Step ($)", value=5000.0, step=1000.0, key="sn_step")
        
        with col3:
            st.markdown("**Working Capital Range**")
            wc_min = st.number_input("Min ($)", value=5000.0, step=1000.0, key="wc_min")
            wc_max = st.number_input("Max ($)", value=50000.0, step=1000.0, key="wc_max")
            wc_step = st.number_input("Step ($)", value=5000.0, step=1000.0, key="wc_step")
        
        buyer_equity_range = (buyer_equity_min, buyer_equity_max, buyer_equity_step)
        seller_note_range = (seller_note_min, seller_note_max, seller_note_step)
        working_capital_range = (wc_min, wc_max, wc_step)
    else:
        # Use defaults
        buyer_equity_range = None
        seller_note_range = None
        working_capital_range = None
    
    # Purchase Price
    st.divider()
    purchase_price = st.number_input(
        "Purchase Price ($)",
        min_value=0.0,
        max_value=5000000.0,
        value=400000.0,
        step=10000.0,
        help="Target purchase price for the business"
    )
    
    # Run Optimization Button
    st.divider()
    
    if st.button("🚀 Run Deal Optimization", type="primary", use_container_width=True):
        # Build base model inputs from session state
        base_model_inputs = {
            'revenue_streams': st.session_state.revenue_streams,
            'payroll_roles': st.session_state.payroll_roles,
            'opex_categories': st.session_state.opex_categories,
            'loan_amount': 0,  # Will be set by optimizer
            'loan_rate': st.session_state.loan_rate,
            'loan_term': st.session_state.loan_term,
            'ar_days': st.session_state.ar_days,
            'ap_days': st.session_state.ap_days,
            'inventory_days': st.session_state.inventory_days,
            'tax_rate': st.session_state.tax_rate,
            'annual_depreciation': st.session_state.annual_depreciation,
            'owner_compensation': st.session_state.owner_compensation,
            'mode': st.session_state.mode,
            'capital_stack': st.session_state.capital_stack,
            'seasonality': st.session_state.seasonality,
            'business_stage': st.session_state.business_stage,
            'model_mode': st.session_state.get('model_mode', 'startup'),
            'working_capital_source': st.session_state.get('working_capital_source', 'buyer_injected')
        }
        
        with st.spinner("🔍 Searching for optimal deal structure... This may take a minute."):
            try:
                results = run_deal_optimization(
                    base_model_inputs=base_model_inputs,
                    purchase_price=purchase_price,
                    objective=objective_value,
                    minimum_dscr=minimum_dscr,
                    minimum_cash_balance=minimum_cash_balance,
                    maximum_loan_amount=maximum_loan_amount,
                    buyer_equity_range=buyer_equity_range,
                    seller_note_range=seller_note_range,
                    working_capital_range=working_capital_range,
                    max_iterations=5000
                )
                
                # Store results in session state
                st.session_state.optimizer_results = results
                
            except Exception as e:
                st.error(f"❌ Optimization failed: {str(e)}")
                return
    
    # Display Results
    if 'optimizer_results' in st.session_state:
        results = st.session_state.optimizer_results
        
        st.divider()
        st.header("📊 Optimization Results")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Scenarios Tested",
                f"{results['total_scenarios_tested']:,}"
            )
        
        with col2:
            st.metric(
                "Valid Scenarios",
                f"{results['valid_scenarios_count']:,}"
            )
        
        with col3:
            success_rate = (results['valid_scenarios_count'] / results['total_scenarios_tested'] * 100) if results['total_scenarios_tested'] > 0 else 0
            st.metric(
                "Success Rate",
                f"{success_rate:.1f}%"
            )
        
        # Best Scenario
        best = results.get('best_scenario')
        
        if best:
            st.divider()
            st.subheader("🏆 Optimal Deal Structure")
            
            st.success(f"**Objective:** {results['objective'].replace('_', ' ').title()}")
            
            # Display optimal structure
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 💰 Capital Structure")
                
                capital_df = pd.DataFrame({
                    "Source": [
                        "Buyer Equity",
                        "Bank Loan",
                        "Seller Note",
                        "Working Capital"
                    ],
                    "Amount": [
                        f"${best['buyer_equity']:,.0f}",
                        f"${best['bank_loan']:,.0f}",
                        f"${best['seller_note']:,.0f}",
                        f"${best['working_capital']:,.0f}"
                    ]
                })
                
                st.table(capital_df)
                
                total_sources = best['buyer_equity'] + best['bank_loan'] + best['seller_note']
                st.caption(f"**Total Sources:** ${total_sources:,.0f}")
            
            with col2:
                st.markdown("### 📈 Performance Metrics")
                
                metrics_df = pd.DataFrame({
                    "Metric": [
                        "DSCR",
                        "Minimum Cash",
                        "Purchase Price",
                        "Owner Income"
                    ],
                    "Value": [
                        f"{best['dscr']:.2f}",
                        f"${best['min_cash']:,.0f}",
                        f"${best['purchase_price']:,.0f}",
                        f"${best['owner_income']:,.0f}"
                    ]
                })
                
                st.table(metrics_df)
            
            # Constraints check
            st.divider()
            st.markdown("### ✅ Constraint Validation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                dscr_status = "✅" if best['dscr'] >= minimum_dscr else "❌"
                st.metric(
                    f"{dscr_status} DSCR",
                    f"{best['dscr']:.2f}",
                    delta=f"{best['dscr'] - minimum_dscr:.2f} vs minimum",
                    delta_color="normal"
                )
            
            with col2:
                cash_status = "✅" if best['min_cash'] >= minimum_cash_balance else "❌"
                st.metric(
                    f"{cash_status} Minimum Cash",
                    f"${best['min_cash']:,.0f}",
                    delta=f"${best['min_cash'] - minimum_cash_balance:,.0f} vs minimum",
                    delta_color="normal"
                )
            
            # Top 10 Scenarios
            if results.get('sorted_scenarios'):
                st.divider()
                st.subheader("📋 Top 10 Scenarios")
                
                top_10_data = []
                for i, scenario in enumerate(results['sorted_scenarios'][:10], 1):
                    top_10_data.append({
                        'Rank': i,
                        'Buyer Equity': f"${scenario['buyer_equity']:,.0f}",
                        'Bank Loan': f"${scenario['bank_loan']:,.0f}",
                        'Seller Note': f"${scenario['seller_note']:,.0f}",
                        'Working Capital': f"${scenario['working_capital']:,.0f}",
                        'DSCR': f"{scenario['dscr']:.2f}",
                        'Min Cash': f"${scenario['min_cash']:,.0f}"
                    })
                
                top_10_df = pd.DataFrame(top_10_data)
                
                st.dataframe(
                    top_10_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.download_button(
                    label="Download Top 10 Scenarios (CSV)",
                    data=top_10_df.to_csv(index=False),
                    file_name="top_10_deal_scenarios.csv",
                    mime="text/csv"
                )
        
        else:
            st.error("❌ No valid scenarios found that meet the constraints.")
            st.info("""
            **Suggestions:**
            - Lower the minimum DSCR requirement
            - Lower the minimum cash balance requirement
            - Increase the search ranges
            - Adjust the purchase price
            """)
