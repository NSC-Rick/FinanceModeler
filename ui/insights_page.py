"""
Insights page with deterministic Red/Yellow/Green flags.

Rule-based analysis with transparent thresholds.
No AI commentary, no subjective language, no composite scoring.
"""

import streamlit as st
from engine.model import build_model
from engine.validation import session_state_to_model_inputs


def render():
    """Render the insights page with rule-based flags."""
    st.title("📊 Insights & Flags")
    
    st.markdown("""
    Deterministic analysis based on transparent rules and thresholds.
    Flags are calculated from your financial model data.
    """)
    
    st.divider()
    
    # Build model to get outputs
    model_inputs = session_state_to_model_inputs(st.session_state)
    
    try:
        with st.spinner("Analyzing model..."):
            outputs = build_model(model_inputs)
        
        # Extract key metrics
        kpis = outputs['kpis']
        income_statement = outputs['income_statement']
        cash_flow_statement = outputs['cash_flow_statement']
        loan_schedule = outputs['loan_schedule']
        
        # Get first period metrics for evaluation
        first_period_kpis = kpis.iloc[0]
        dscr = first_period_kpis.get('dscr', 0)
        gross_margin_pct = first_period_kpis.get('gross_margin_pct', 0) / 100  # Convert to decimal
        
        # Calculate cash after debt and owner
        net_income = income_statement['net_income'].iloc[0]
        debt_service = loan_schedule['payment'].iloc[0]
        cash_after_debt = net_income - debt_service
        
        owner_comp_config = model_inputs.get('owner_compensation', {'mode': 'distribution', 'amount': 0.0})
        owner_comp_mode = owner_comp_config.get('mode', 'distribution')
        owner_comp_annual = owner_comp_config.get('amount', 0.0)
        
        if model_inputs['time_mode'] == 'monthly':
            owner_comp_per_period = owner_comp_annual / 12
        else:
            owner_comp_per_period = owner_comp_annual
        
        if owner_comp_mode == 'distribution':
            cash_after_debt_and_owner = cash_after_debt - owner_comp_per_period
        else:
            cash_after_debt_and_owner = cash_after_debt
        
        # Operating cash flow
        operating_cash_flow = cash_flow_statement['operating_cash_flow'].iloc[0]
        
        # Revenue for ratio calculations
        revenue = income_statement['revenue'].iloc[0]
        
        # Rent calculation (find rent in opex_items)
        rent_amount = 0
        for item in model_inputs.get('opex_items', []):
            if item.get('name', '').lower() == 'rent':
                rent_amount = item.get('amount', 0)
                break
        
        rent_to_revenue_ratio = rent_amount / revenue if revenue > 0 else 0
        
        # Advanced mode checks
        mode = model_inputs.get('mode', 'Basic')
        is_advanced = (mode == 'Advanced')
        
        # Funding gap (Advanced only)
        funding_gap = 0
        if is_advanced:
            capital_stack = model_inputs.get('capital_stack', {})
            if capital_stack.get('enabled', False):
                uses = capital_stack.get('uses', {})
                sources = capital_stack.get('sources', {})
                
                total_uses = sum([
                    uses.get('purchase_price', 0),
                    uses.get('inventory_adjustment', 0),
                    uses.get('closing_costs', 0),
                    uses.get('working_capital', 0),
                    uses.get('capex', 0)
                ])
                
                total_sources = sum([
                    sources.get('buyer_equity', 0),
                    sources.get('community_equity', 0),
                    sources.get('donations', 0),
                    sources.get('bank_loan', {}).get('amount', 0),
                    sources.get('seller_note', {}).get('amount', 0)
                ])
                
                funding_gap = total_sources - total_uses
        
        # AR days (Advanced only)
        ar_days = model_inputs.get('ar_days', 0)
        
        # Equity injection ratio (Advanced only)
        equity_ratio = 0
        if is_advanced:
            capital_stack = model_inputs.get('capital_stack', {})
            if capital_stack.get('enabled', False):
                uses = capital_stack.get('uses', {})
                sources = capital_stack.get('sources', {})
                
                total_uses = sum([
                    uses.get('purchase_price', 0),
                    uses.get('inventory_adjustment', 0),
                    uses.get('closing_costs', 0),
                    uses.get('working_capital', 0),
                    uses.get('capex', 0)
                ])
                
                total_equity = sum([
                    sources.get('buyer_equity', 0),
                    sources.get('community_equity', 0),
                    sources.get('donations', 0)
                ])
                
                equity_ratio = total_equity / total_uses if total_uses > 0 else 0
        
        # ========================================
        # RED FLAGS
        # ========================================
        red_flags = []
        
        # Rule: DSCR < 1.0
        if dscr < 1.0:
            red_flags.append(f"DSCR below 1.0 (current: {dscr:.2f}). Debt service exceeds available cash flow.")
        
        # Rule: Cash after debt and owner < 0
        if cash_after_debt_and_owner < 0:
            red_flags.append(f"Negative cash after debt and owner compensation (${cash_after_debt_and_owner:,.2f}). Business cannot cover obligations.")
        
        # Rule: Operating cash flow < 0
        if operating_cash_flow < 0:
            red_flags.append(f"Negative operating cash flow (${operating_cash_flow:,.2f}). Operations are consuming cash.")
        
        # Rule: Advanced mode AND funding gap != 0
        if is_advanced and funding_gap != 0:
            if funding_gap > 0:
                red_flags.append(f"Capital stack funding surplus (${funding_gap:,.2f}). Sources exceed uses.")
            else:
                red_flags.append(f"Capital stack funding shortfall (${abs(funding_gap):,.2f}). Uses exceed sources.")
        
        # ========================================
        # YELLOW FLAGS
        # ========================================
        yellow_flags = []
        
        # Rule: 1.0 <= DSCR < 1.20
        if 1.0 <= dscr < 1.20:
            yellow_flags.append(f"DSCR between 1.0 and 1.20 (current: {dscr:.2f}). Minimal debt service coverage.")
        
        # Rule: Rent / Revenue > 0.12
        if rent_to_revenue_ratio > 0.12:
            yellow_flags.append(f"Rent exceeds 12% of revenue (current: {rent_to_revenue_ratio*100:.1f}%). High occupancy cost.")
        
        # Rule: Gross margin < 0.30
        if gross_margin_pct < 0.30:
            yellow_flags.append(f"Gross margin below 30% (current: {gross_margin_pct*100:.1f}%). Limited pricing power or high COGS.")
        
        # Rule: Advanced mode AND AR days > 30
        if is_advanced and ar_days > 30:
            yellow_flags.append(f"Accounts receivable days exceed 30 (current: {ar_days}). Slow customer payment cycle.")
        
        # ========================================
        # GREEN SIGNALS
        # ========================================
        green_signals = []
        
        # Rule: DSCR >= 1.25
        if dscr >= 1.25:
            green_signals.append(f"DSCR at or above 1.25 (current: {dscr:.2f}). Strong debt service coverage.")
        
        # Rule: Cash after debt and owner >= 0
        if cash_after_debt_and_owner >= 0:
            green_signals.append(f"Positive cash after debt and owner compensation (${cash_after_debt_and_owner:,.2f}). Business covers all obligations.")
        
        # Rule: Operating cash flow > 0
        if operating_cash_flow > 0:
            green_signals.append(f"Positive operating cash flow (${operating_cash_flow:,.2f}). Operations generate cash.")
        
        # Rule: Advanced mode AND equity injection >= 0.20
        if is_advanced and equity_ratio >= 0.20:
            green_signals.append(f"Equity injection at or above 20% (current: {equity_ratio*100:.1f}%). Strong equity cushion.")
        
        # ========================================
        # DISPLAY
        # ========================================
        
        # Red Flags Section
        st.markdown("### 🔴 Red Flags")
        if red_flags:
            for flag in red_flags:
                st.error(f"🔴 {flag}")
        else:
            st.success("✅ No red flags detected.")
        
        st.divider()
        
        # Yellow Flags Section
        st.markdown("### 🟡 Yellow Flags")
        if yellow_flags:
            for flag in yellow_flags:
                st.warning(f"🟡 {flag}")
        else:
            st.info("✅ No yellow flags detected.")
        
        st.divider()
        
        # Green Signals Section
        st.markdown("### 🟢 Green Signals")
        if green_signals:
            for signal in green_signals:
                st.success(f"🟢 {signal}")
        else:
            st.info("ℹ️ No green signals detected.")
        
        st.divider()
        
        # Rule Reference
        with st.expander("📋 Flag Rules Reference"):
            st.markdown("""
            **Red Flag Thresholds:**
            - DSCR < 1.0
            - Cash after debt and owner < $0
            - Operating cash flow < $0
            - Capital stack funding gap ≠ $0 (Advanced mode only)
            
            **Yellow Flag Thresholds:**
            - 1.0 ≤ DSCR < 1.20
            - Rent / Revenue > 12%
            - Gross margin < 30%
            - AR days > 30 (Advanced mode only)
            
            **Green Signal Thresholds:**
            - DSCR ≥ 1.25
            - Cash after debt and owner ≥ $0
            - Operating cash flow > $0
            - Equity injection ≥ 20% (Advanced mode only)
            
            *All thresholds are deterministic and rule-based. No subjective analysis.*
            """)
        
    except Exception as e:
        st.error(f"Error analyzing model: {str(e)}")
        st.info("Please ensure all required inputs are configured in the other pages.")
