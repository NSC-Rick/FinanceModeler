import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from engine.model import build_model
from engine.validation import validate_scenario_json
from utils.formatters import safe_currency, safe_ratio, safe_percentage
from ui.report_view import render_report
from analysis.financial_metrics import compute_financial_metrics


def render():
    """Render the review page with financial statements and charts."""
    st.title("Review & Analysis")
    
    st.markdown("""
    Review your complete financial model including income statement, cash flow statement, and key metrics.
    """)
    
    # Generate Report button
    if st.button("📄 Generate Print Report", type="primary", help="Create a print-friendly report view"):
        st.session_state.show_report = True
    
    # Show report if requested
    if st.session_state.get('show_report', False):
        st.divider()
        st.markdown("## 📄 Print Report View")
        st.caption("This view is optimized for printing or PDF export. Use your browser's print function (Ctrl+P or Cmd+P).")
        
        if st.button("← Back to Analysis View"):
            st.session_state.show_report = False
            st.rerun()
    
    model_inputs = {
        'time_mode': st.session_state.time_mode,
        'periods': st.session_state.periods,
        'revenue_streams': st.session_state.revenue_streams,
        'global_cogs_pct': st.session_state.global_cogs_pct,
        'payroll_roles': st.session_state.payroll_roles,
        'opex_items': st.session_state.opex_items,
        'loan_principal': st.session_state.loan_principal,
        'loan_annual_rate': st.session_state.loan_annual_rate,
        'loan_term_months': st.session_state.loan_term_months,
        'loan_start_period': st.session_state.loan_start_period,
        'ar_days': st.session_state.ar_days,
        'ap_days': st.session_state.ap_days,
        'inventory_days': st.session_state.inventory_days,
        'tax_rate': st.session_state.tax_rate,
        'annual_depreciation': st.session_state.annual_depreciation,
        'owner_compensation': st.session_state.owner_compensation,
        'mode': st.session_state.mode,
        'capital_stack': st.session_state.capital_stack,
        'seasonality': st.session_state.seasonality
    }
    
    try:
        with st.spinner("Building financial model..."):
            outputs = build_model(model_inputs)
        
        # Store summary metrics in session_state for Modeler page
        income_statement = outputs['income_statement']
        cash_flow_statement = outputs['cash_flow']
        loan_schedule = outputs['loan_schedule']
        kpis = outputs['kpis']
        
        # Compute canonical financial metrics (single source of truth)
        owner_comp_config = model_inputs.get('owner_compensation', {'mode': 'distribution', 'amount': 0.0})
        canonical_metrics = compute_financial_metrics(
            income_statement,
            cash_flow_statement,
            loan_schedule,
            owner_comp_config,
            model_inputs['time_mode']
        )
        
        # Store DataFrames in session state for Excel export
        # Income statement transposed (rows = line items, columns = periods)
        income_transposed = income_statement.T
        income_transposed.columns = [f'Period {i}' for i in income_transposed.columns]
        income_transposed.index.name = 'Line Item'
        st.session_state.income_statement_df = income_transposed
        
        # Cash flow transposed
        if 'cash_flow' in outputs:
            cash_flow = outputs['cash_flow']
            cash_flow_transposed = cash_flow.T
            cash_flow_transposed.columns = [f'Period {i}' for i in cash_flow_transposed.columns]
            cash_flow_transposed.index.name = 'Line Item'
            st.session_state.cash_flow_df = cash_flow_transposed
        
        # Store canonical DSCR series
        st.session_state.dscr_series = canonical_metrics['dscr_series']
        
        # Calculate Year 1 metrics using canonical source
        if st.session_state.time_mode == 'monthly':
            year1_periods = min(12, len(income_statement))
            year1_revenue = income_statement['revenue'][:year1_periods].sum()
            year1_operating_expenses = income_statement['operating_expenses'][:year1_periods].sum()
            year1_net_income = income_statement['net_income'][:year1_periods].sum()
            year1_debt_service = loan_schedule['payment'][:year1_periods].sum()
            year1_cash_flow = year1_net_income - year1_debt_service
            year1_ebitda = income_statement['ebitda'][:year1_periods].sum()
            # Use canonical DSCR calculation
            year1_dscr = year1_ebitda / year1_debt_service if year1_debt_service > 0 else None
        else:
            year1_revenue = income_statement['revenue'].iloc[0]
            year1_operating_expenses = income_statement['operating_expenses'].iloc[0]
            year1_net_income = income_statement['net_income'].iloc[0]
            year1_debt_service = loan_schedule['payment'].iloc[0]
            year1_cash_flow = year1_net_income - year1_debt_service
            year1_ebitda = income_statement['ebitda'].iloc[0]
            # Use canonical DSCR calculation
            year1_dscr = year1_ebitda / year1_debt_service if year1_debt_service > 0 else None
        
        # Store in session_state for Modeler
        st.session_state.review_summary_metrics = {
            'year1_revenue': year1_revenue,
            'year1_operating_expenses': year1_operating_expenses,
            'year1_net_income': year1_net_income,
            'year1_debt_service': year1_debt_service,
            'year1_cash_flow': year1_cash_flow,
            'year1_dscr': year1_dscr
        }
        
        # If report view requested, render report and return
        if st.session_state.get('show_report', False):
            render_report(outputs, model_inputs)
            return
        
        st.success("✅ Model built successfully!")
        
        st.divider()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Income Statement",
            "💰 Cash Flow",
            "🏦 Loan Schedule",
            "📈 KPIs",
            "📉 Charts"
        ])
        
        with tab1:
            # Force scroll to top when Income Statement tab is rendered
            st.markdown(
                """
                <script>
                    window.scrollTo(0, 0);
                </script>
                """,
                unsafe_allow_html=True
            )
            
            st.subheader("Income Statement")
            
            # Add toggle for dollar vs % of revenue view
            income_view = st.radio(
                "Display Format:",
                options=['Dollar', '% of Revenue'],
                horizontal=True,
                key='income_view_toggle'
            )
            
            income_statement = outputs['income_statement'].copy()
            
            # Transpose: line items as rows, periods as columns
            income_transposed = income_statement.T
            
            # Rename columns to Period 0, Period 1, etc.
            income_transposed.columns = [f'Period {i}' for i in income_transposed.columns]
            income_transposed.index.name = 'Line Item'
            
            # Convert to % of revenue if selected
            if income_view == '% of Revenue':
                income_display = income_transposed.copy()
                
                # Get revenue row for each period
                revenue_row = income_statement['revenue']
                
                # Convert each column (period) to % of revenue
                for col_idx, period in enumerate(income_display.columns):
                    revenue_value = revenue_row.iloc[col_idx]
                    
                    if revenue_value != 0:
                        # Divide each line item by revenue for this period
                        income_display[period] = (income_transposed[period] / revenue_value) * 100
                    else:
                        # Avoid divide by zero - set to 0
                        income_display[period] = 0
                
                st.dataframe(
                    income_display.style.format("{:.2f}%"),
                    use_container_width=True
                )
                
                download_data = income_display.to_csv()
                download_filename = "income_statement_percent.csv"
            else:
                # Dollar view
                income_display = income_transposed
                
                st.dataframe(
                    income_display.style.format("${:,.2f}"),
                    use_container_width=True
                )
                
                download_data = income_display.to_csv()
                download_filename = "income_statement.csv"
            
            st.download_button(
                label=f"Download Income Statement ({income_view}) (CSV)",
                data=download_data,
                file_name=download_filename,
                mime="text/csv"
            )
            
            # Overlay section: Debt Service and Owner Compensation
            st.divider()
            st.markdown("### Cash Flow Analysis")
            st.caption("Supplemental analysis showing debt service and owner compensation impact on cash")
            
            # Get loan schedule for debt service calculation
            loan_schedule = outputs['loan_schedule']
            
            # Get owner compensation configuration
            owner_comp_config = st.session_state.owner_compensation
            owner_comp_mode = owner_comp_config.get('mode', 'distribution')
            owner_comp_annual = owner_comp_config.get('amount', 0.0)
            
            # Convert owner comp to per-period
            if st.session_state.time_mode == 'monthly':
                owner_comp_per_period = owner_comp_annual / 12
            else:
                owner_comp_per_period = owner_comp_annual
            
            # Build overlay dataframe
            overlay_data = {}
            
            # Get Net Income from income statement
            net_income_row = income_statement['net_income']
            
            # Total debt service per period (principal + interest)
            total_debt_service = loan_schedule['payment']
            
            # Calculate cash metrics
            cash_after_debt = net_income_row - total_debt_service
            
            # Only subtract owner comp if in distribution mode
            if owner_comp_mode == 'distribution':
                cash_after_debt_and_owner = cash_after_debt - owner_comp_per_period
            else:
                # In payroll mode, owner comp already in income statement
                cash_after_debt_and_owner = cash_after_debt
            
            # Build overlay dataframe with same structure as income statement
            overlay_df = pd.DataFrame({
                'Net Income': net_income_row,
                'Debt Service (Principal + Interest)': total_debt_service,
                'Cash After Debt': cash_after_debt,
                'Owner Compensation': owner_comp_per_period if owner_comp_mode == 'distribution' else 0,
                'Cash After Debt & Owner': cash_after_debt_and_owner
            })
            
            # Transpose to match income statement format
            overlay_transposed = overlay_df.T
            overlay_transposed.columns = [f'Period {i}' for i in overlay_transposed.columns]
            overlay_transposed.index.name = 'Line Item'
            
            # Display based on selected view
            if income_view == '% of Revenue':
                overlay_display = overlay_transposed.copy()
                revenue_row = income_statement['revenue']
                
                for col_idx, period in enumerate(overlay_display.columns):
                    revenue_value = revenue_row.iloc[col_idx]
                    if revenue_value != 0:
                        overlay_display[period] = (overlay_transposed[period] / revenue_value) * 100
                    else:
                        overlay_display[period] = 0
                
                st.dataframe(
                    overlay_display.style.format("{:.2f}%"),
                    use_container_width=True
                )
            else:
                st.dataframe(
                    overlay_transposed.style.format("${:,.2f}"),
                    use_container_width=True
                )
            
            # Add explanatory note
            if owner_comp_mode == 'payroll':
                st.info("ℹ️ Owner compensation is treated as **Payroll** and already included in the Income Statement above. Cash After Debt & Owner equals Cash After Debt.")
            else:
                st.info(f"ℹ️ Owner compensation (${owner_comp_annual:,.2f}/year) is treated as **Distribution** and deducted from cash after debt service.")
        
        with tab2:
            st.subheader("Cash Flow Statement")
            
            cash_flow = outputs['cash_flow_statement'].copy()
            
            # Transpose: line items as rows, periods as columns
            cash_flow_transposed = cash_flow.T
            
            # Rename columns to Period 0, Period 1, etc.
            cash_flow_transposed.columns = [f'Period {i}' for i in cash_flow_transposed.columns]
            cash_flow_transposed.index.name = 'Line Item'
            
            st.dataframe(
                cash_flow_transposed.style.format("${:,.2f}"),
                use_container_width=True
            )
            
            st.download_button(
                label="Download Cash Flow (CSV)",
                data=cash_flow_transposed.to_csv(),
                file_name="cash_flow.csv",
                mime="text/csv"
            )
        
        with tab3:
            st.subheader("Loan Amortization Schedule")
            
            loan_schedule = outputs['loan_schedule'].copy()
            
            st.dataframe(
                loan_schedule.style.format("${:,.2f}"),
                use_container_width=True
            )
            
            st.download_button(
                label="Download Loan Schedule (CSV)",
                data=loan_schedule.to_csv(),
                file_name="loan_schedule.csv",
                mime="text/csv"
            )
        
        with tab4:
            st.subheader("Key Performance Indicators")
            
            kpis = outputs['kpis'].copy()
            kpis.index.name = 'Period'
            
            # Use safe formatters to handle None/NaN values
            format_dict = {
                'ebitda': lambda x: safe_currency(x),
                'debt_service': lambda x: safe_currency(x),
                'dscr': lambda x: safe_ratio(x),
                'ending_cash': lambda x: safe_currency(x)
            }
            
            if 'net_income' in kpis.columns:
                format_dict['net_income'] = lambda x: safe_currency(x)
                format_dict['taxes'] = lambda x: safe_currency(x)
                format_dict['net_margin'] = lambda x: safe_percentage(x)
            
            st.dataframe(
                kpis.style.format(format_dict),
                use_container_width=True
            )
            
            st.markdown("### 🎯 Key Underwriting Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Use canonical metrics for DSCR
                avg_dscr = canonical_metrics['avg_dscr']
                total_debt_service = canonical_metrics['total_debt_service']
                
                if total_debt_service == 0 or avg_dscr is None:
                    # Debt-free scenario
                    st.metric(
                        label="⭐ Average DSCR",
                        value="—",
                        help="Debt Service Coverage Ratio = EBITDA / Total Debt Service. No debt obligations."
                    )
                    st.success("🟢 Debt Free")
                    st.caption("No debt obligations")
                else:
                    # Use canonical average DSCR
                    st.metric(
                        label="⭐ Average DSCR",
                        value=f"{avg_dscr:.2f}",
                        help="Debt Service Coverage Ratio = EBITDA / Total Debt Service. Lenders typically require 1.25+"
                    )
                    
                    if avg_dscr >= 1.25:
                        st.success("✅ Strong debt coverage")
                    elif avg_dscr >= 1.0:
                        st.warning("⚠️ Marginal debt coverage")
                    else:
                        st.error("❌ Insufficient debt coverage")
            
            with col2:
                if 'break_even_revenue' in kpis.columns:
                    break_even = kpis['break_even_revenue'].iloc[0]
                    if st.session_state.time_mode == 'monthly':
                        total_revenue = outputs['pnl_statement']['revenue'].sum()
                    else:
                        total_revenue = outputs['pnl_statement']['revenue'].iloc[0] if len(outputs['pnl_statement']) > 0 else 0
                    
                    st.metric(
                        label="💰 Break-Even Revenue (Annual)",
                        value=safe_currency(break_even, decimals=0, placeholder="N/A"),
                        help="Annual revenue needed to cover all fixed costs, owner salary, and debt service"
                    )
                    
                    if not pd.isna(break_even) and total_revenue > 0:
                        if st.session_state.time_mode == 'monthly':
                            coverage = (total_revenue / break_even) if break_even > 0 else 0
                        else:
                            coverage = (total_revenue / break_even) if break_even > 0 else 0
                        
                        if coverage >= 1.5:
                            st.success(f"✅ {coverage:.1f}x coverage")
                        elif coverage >= 1.0:
                            st.warning(f"⚠️ {coverage:.1f}x coverage")
                        else:
                            st.error(f"❌ {coverage:.1f}x coverage")
            
            with col3:
                if 'contribution_margin_pct' in kpis.columns:
                    avg_contrib_margin = kpis['contribution_margin_pct'].mean()
                    st.metric(
                        label="📊 Contribution Margin %",
                        value=f"{avg_contrib_margin:.1%}",
                        help="(Revenue - Variable Costs) / Revenue. Higher is better for covering fixed costs."
                    )
                    if avg_contrib_margin >= 0.40:
                        st.success("✅ Strong margin")
                    elif avg_contrib_margin >= 0.25:
                        st.info("ℹ️ Moderate margin")
                    else:
                        st.warning("⚠️ Thin margin")
            
            st.divider()
            
            st.markdown("### 💵 Financial Performance")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                final_cash = kpis['ending_cash'].iloc[-1]
                st.metric(
                    label="Final Ending Cash",
                    value=safe_currency(final_cash)
                )
            
            with col2:
                if 'net_income' in kpis.columns:
                    final_net_income = kpis['net_income'].iloc[-1]
                    st.metric(
                        label="Final Net Income",
                        value=safe_currency(final_net_income)
                    )
            
            with col3:
                if 'gross_margin' in kpis.columns:
                    avg_gross_margin = kpis['gross_margin'].mean()
                    st.metric(
                        label="Avg Gross Margin %",
                        value=safe_percentage(avg_gross_margin, decimals=1)
                    )
            
            with col4:
                if 'taxes' in kpis.columns:
                    total_taxes = kpis['taxes'].sum()
                    st.metric(
                        label="Total Taxes (3Y)",
                        value=safe_currency(total_taxes)
                    )
            
            st.download_button(
                label="Download KPIs (CSV)",
                data=kpis.to_csv(),
                file_name="kpis.csv",
                mime="text/csv"
            )
        
        with tab5:
            st.subheader("Visualizations")
            
            fig_revenue = go.Figure()
            
            # Add actual revenue line
            fig_revenue.add_trace(go.Scatter(
                x=list(range(st.session_state.periods)),
                y=outputs['income_statement']['revenue'].values,
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # If startup ramp is enabled, show full steady-state revenue
            startup_ramp = st.session_state.get('startup_ramp_months', 0)
            if startup_ramp > 0 and st.session_state.time_mode == 'monthly':
                # Calculate full revenue without ramp
                full_revenue = []
                for period in range(st.session_state.periods):
                    if startup_ramp > 0 and period < startup_ramp:
                        ramp_factor = (period + 1) / startup_ramp
                        full_rev = outputs['income_statement']['revenue'].values[period] / ramp_factor if ramp_factor > 0 else 0
                    else:
                        full_rev = outputs['income_statement']['revenue'].values[period]
                    full_revenue.append(full_rev)
                
                fig_revenue.add_trace(go.Scatter(
                    x=list(range(st.session_state.periods)),
                    y=full_revenue,
                    mode='lines',
                    name='Full Revenue (Steady-State)',
                    line=dict(color='#1f77b4', width=1, dash='dash'),
                    opacity=0.5
                ))
                
                # Add shaded ramp period
                fig_revenue.add_vrect(
                    x0=0,
                    x1=startup_ramp,
                    fillcolor="lightgray",
                    opacity=0.2,
                    line_width=0,
                    annotation_text=f"Ramp Period ({startup_ramp} months)",
                    annotation_position="top left"
                )
            
            fig_revenue.update_layout(
                title="Revenue Trend",
                xaxis_title="Period",
                yaxis_title="Revenue ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
            
            fig_cash = go.Figure()
            fig_cash.add_trace(go.Scatter(
                x=list(range(st.session_state.periods)),
                y=outputs['cash_flow_statement']['ending_cash'].values,
                mode='lines+markers',
                name='Ending Cash',
                line=dict(color='#2ca02c', width=2),
                fill='tozeroy'
            ))
            fig_cash.update_layout(
                title="Ending Cash Balance",
                xaxis_title="Period",
                yaxis_title="Cash ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig_cash, use_container_width=True)
            
            dscr_data = kpis[kpis['dscr'] > 0]['dscr']
            if len(dscr_data) > 0:
                fig_dscr = go.Figure()
                fig_dscr.add_trace(go.Scatter(
                    x=dscr_data.index.tolist(),
                    y=dscr_data.values,
                    mode='lines+markers',
                    name='DSCR',
                    line=dict(color='#ff7f0e', width=2)
                ))
                fig_dscr.add_hline(
                    y=1.25,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Target DSCR = 1.25"
                )
                fig_dscr.update_layout(
                    title="Debt Service Coverage Ratio (DSCR)",
                    xaxis_title="Period",
                    yaxis_title="DSCR",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_dscr, use_container_width=True)
            else:
                st.info("No debt service payments in this model period.")
    
    except Exception as e:
        st.error(f"Error building model: {str(e)}")
        st.exception(e)
