import streamlit as st


def render():
    """Render the revenue configuration page."""
    st.title("Revenue Streams")
    
    st.markdown("""
    Configure your revenue streams. Each stream has its own price, volume, and growth rate.
    You can optionally override the global COGS percentage for specific streams.
    """)
    
    st.divider()
    
    st.subheader("Global COGS Settings")
    
    global_cogs_pct = st.number_input(
        "Default COGS Percentage",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.global_cogs_pct,
        step=0.01,
        format="%.2f",
        help="Default cost of goods sold as a percentage of revenue (e.g., 0.30 = 30%)"
    )
    st.session_state.global_cogs_pct = global_cogs_pct
    
    st.divider()
    
    # Seasonality Controls
    st.subheader("Revenue Seasonality")
    
    st.markdown("""
    Apply seasonal patterns to revenue distribution across months.
    Seasonality affects revenue timing, AR calculations, and inventory proportionally.
    """)
    
    # Retail preset weights (typical retail seasonality)
    RETAIL_PRESET = [6.5, 6.0, 7.5, 8.0, 8.5, 9.0, 9.5, 9.0, 8.0, 9.5, 11.0, 17.5]  # Sums to 100
    
    seasonality_mode = st.radio(
        "Seasonality Mode",
        ["OFF", "Retail Preset", "Custom"],
        index=["OFF", "Retail Preset", "Custom"].index(st.session_state.seasonality['mode']),
        horizontal=True,
        help="OFF: Even distribution. Retail: Holiday-weighted. Custom: Define your own (Advanced mode only)"
    )
    
    # Restrict Custom mode to Advanced
    if seasonality_mode == "Custom" and st.session_state.mode == "Basic":
        st.warning("⚠️ Custom seasonality requires Advanced mode. Switch to Advanced mode in Financing page.")
        seasonality_mode = st.session_state.seasonality['mode']  # Revert to previous
    
    st.session_state.seasonality['mode'] = seasonality_mode
    st.session_state.seasonality['enabled'] = (seasonality_mode != "OFF")
    
    if seasonality_mode == "Retail Preset":
        st.info("📊 **Retail Preset Active:** Revenue weighted toward Q4 holidays (Nov: 11%, Dec: 17.5%)")
        
        # Show visualization
        import pandas as pd
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        chart_data = pd.DataFrame({
            'Month': months,
            'Weight (%)': RETAIL_PRESET
        })
        st.bar_chart(chart_data.set_index('Month'))
        
    elif seasonality_mode == "Custom":
        st.info("🔧 **Custom Seasonality:** Define monthly revenue weights (will auto-normalize to 100%)")
        
        st.markdown("**Monthly Revenue Weights (%)**")
        
        # Create 3 rows of 4 months each
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        custom_weights = []
        
        for row in range(3):
            cols = st.columns(4)
            for col_idx in range(4):
                month_idx = row * 4 + col_idx
                with cols[col_idx]:
                    weight = st.number_input(
                        months[month_idx],
                        min_value=0.0,
                        max_value=100.0,
                        value=st.session_state.seasonality['custom_weights'][month_idx],
                        step=0.5,
                        key=f"season_weight_{month_idx}",
                        help=f"Revenue weight for {months[month_idx]}"
                    )
                    custom_weights.append(weight)
        
        # Auto-normalize
        total_weight = sum(custom_weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight * 100 for w in custom_weights]
            st.session_state.seasonality['custom_weights'] = normalized_weights
            
            st.caption(f"**Total:** {total_weight:.1f}% → Normalized to 100%")
            
            # Show visualization
            chart_data = pd.DataFrame({
                'Month': months,
                'Weight (%)': normalized_weights
            })
            st.bar_chart(chart_data.set_index('Month'))
        else:
            st.warning("⚠️ Total weight is 0. Please enter at least one non-zero value.")
    
    st.divider()
    
    st.subheader("Revenue Streams")
    
    for idx, stream in enumerate(st.session_state.revenue_streams):
        with st.expander(f"**{stream['name']}**", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Stream Name",
                    value=stream['name'],
                    key=f"rev_name_{idx}"
                )
                
                price = st.number_input(
                    "Price per Unit",
                    min_value=0.0,
                    value=stream['price'],
                    step=1.0,
                    key=f"rev_price_{idx}",
                    help="Price per unit of product/service"
                )
                
                volume = st.number_input(
                    "Initial Volume",
                    min_value=0.0,
                    value=stream['volume'],
                    step=1.0,
                    key=f"rev_volume_{idx}",
                    help=f"Initial {'monthly' if st.session_state.time_mode == 'monthly' else 'annual'} volume"
                )
            
            with col2:
                growth_rate = st.number_input(
                    f"{'Annual' if st.session_state.time_mode == 'monthly' else 'Annual'} Growth Rate",
                    min_value=-1.0,
                    max_value=10.0,
                    value=stream['growth_rate'],
                    step=0.01,
                    format="%.2f",
                    key=f"rev_growth_{idx}",
                    help="Annual growth rate (e.g., 0.10 = 10% per year)"
                )
                
                use_override = st.checkbox(
                    "Override COGS %",
                    value=stream['cogs_override'] is not None,
                    key=f"rev_cogs_override_check_{idx}"
                )
                
                if use_override:
                    cogs_override = st.number_input(
                        "COGS Percentage",
                        min_value=0.0,
                        max_value=1.0,
                        value=stream['cogs_override'] if stream['cogs_override'] is not None else global_cogs_pct,
                        step=0.01,
                        format="%.2f",
                        key=f"rev_cogs_override_{idx}"
                    )
                else:
                    cogs_override = None
            
            st.session_state.revenue_streams[idx] = {
                'name': name,
                'price': price,
                'volume': volume,
                'growth_rate': growth_rate,
                'cogs_override': cogs_override
            }
            
            if st.button(f"Remove {name}", key=f"remove_rev_{idx}"):
                st.session_state.revenue_streams.pop(idx)
                st.rerun()
    
    st.divider()
    
    if st.button("➕ Add Revenue Stream"):
        st.session_state.revenue_streams.append({
            'name': f'Stream {len(st.session_state.revenue_streams) + 1}',
            'price': 100.0,
            'volume': 100.0,
            'growth_rate': 0.10,
            'cogs_override': None
        })
        st.rerun()
