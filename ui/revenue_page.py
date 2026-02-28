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
