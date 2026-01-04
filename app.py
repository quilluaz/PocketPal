import streamlit as st
import pandas as pd
import pandas as pd

st.set_page_config(
    page_title="Pocketpal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.auth import init_session_state, is_authenticated, render_auth_page, logout, get_current_user_id
from src.db_connector import get_transactions, insert_transactions, delete_transaction, get_holdings, insert_holding, delete_holding, get_existing_signatures, get_profile, update_profile_currency
from src.etl_pipeline import process_csv
from src.market_data import calculate_holdings_value, get_total_portfolio_value, validate_ticker, get_usd_php_rate
from src.visuals import create_sankey_diagram, create_spending_by_category_chart, create_spending_trend_chart, create_holdings_chart, calculate_kpis

def main():
    # Inject Custom CSS for Font
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Space Grotesk', sans-serif;
            }
            
            /* Sticky Header Styles */
            /* Target the horizontal block that contains our marker */
            div[data-testid="stHorizontalBlock"]:has(div#sticky-header-marker) {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                z-index: 999990;
                background-color: #0e1117; /* Default Streamlit Dark */
                padding: 1rem 2rem;
                border-bottom: 1px solid #30333d;
            }
            
            /* Adjust main content padding to not hide behind header */
            .main .block-container {
                padding-top: 3rem !important; /* Minimal padding */
            }
            
            /* Hide Streamlit default header/hamburger and other top elements */
            header[data-testid="stHeader"],
            div[data-testid="stDecoration"],
            div[data-testid="stToolbar"],
            div[data-testid="stStatusWidget"],
            .stDeployButton {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
            }
            
            /* Additional safety for different streamlit versions */
            .stApp > header {
                display: none !important;
            }
            
            /* Ensure our header is absolutely on top */
            div[data-testid="stHorizontalBlock"]:has(div#sticky-header-marker) {
                top: 0 !important;
                z-index: 999990 !important; /* Lowered to sit below modals */
            }

            /* -- BUTTON STYLING (Green Theme) -- */
            
            /* Primary Button (Login, Sign Up, etc) */
            div.stButton > button[kind="primary"],
            div[data-testid="stForm"] button[kind="primary"],
            button[kind="primary"] {
                background-color: #0d3b10 !important; /* Darker Green (Default) */
                border-color: #0d3b10 !important;
                color: white !important;
                transition: all 0.2s ease;
            }
            
            div.stButton > button[kind="primary"]:hover,
            div[data-testid="stForm"] button[kind="primary"]:hover,
            button[kind="primary"]:hover {
                background-color: #1B5E20 !important; /* Lighter Green (Hover) */
                border-color: #1B5E20 !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
                color: white !important;
            }
            
            div.stButton > button[kind="primary"]:focus,
            div[data-testid="stForm"] button[kind="primary"]:focus,
            button[kind="primary"]:focus {
                box-shadow: 0 0 0 2px rgba(27, 94, 32, 0.4) !important;
                border-color: #1B5E20 !important;
                color: white !important;
            }

            /* -- INPUT FIELD STYLING -- */
            
            /* Target the input container for border/box-shadow focus changes */
            div[data-baseweb="input"] {
                background-color: transparent !important;
                border-radius: 4px;
            }
            
            /* Aggressive fix for "Dark Spot" / Eye Icon Background */
            div[data-baseweb="input"] > div:last-child,
            div[data-baseweb="input"] > div:last-child > div,
            div[data-baseweb="input"] button {
                background-color: transparent !important;
                border: none !important;
            }
            
            /* When the input is focused, change the border of the container */
            div[data-baseweb="input"]:focus-within {
                border-color: #1B5E20 !important;
                box-shadow: 0 0 0 1px #1B5E20 !important;
            }
            
            /* Also ensure the actual input element has no conflicting styles */
            div[data-testid="stTextInput"] input,
            div[data-testid="stNumberInput"] input {
                color: inherit;
                background-color: transparent !important;
            }
        </style>
    """, unsafe_allow_html=True)

    init_session_state()
    
    if not is_authenticated():
        render_auth_page()
        return
    
    render_main_content()


def render_header():
    # Get profile to see current setting
    user_id = get_current_user_id()
    if not user_id: return
    
    profile = get_profile(user_id)
    current_currency = profile.get("currency", "USD")
    user = st.session_state.get("user")
    
    # Create the sticky header container
    # We put a marker div inside col1 so our CSS can find the horizontal block
    with st.container():
        col1, col2, col3, col4 = st.columns([6, 1, 2, 1])
        
        with col1:
            # Combine marker and logo to prevent Streamlit from adding vertical space between them
            st.markdown("""
                <div id="sticky-header-marker"></div>
                <div style='
                    display: flex; 
                    align-items: center; 
                    height: 45px; 
                    font-size: 24px; 
                    font-weight: 700; 
                    white-space: nowrap;
                    margin: 0;
                '>
                    Pocketpal
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Use a Popover for a cleaner "Dropdown" UI without text input
            with st.popover(current_currency, use_container_width=True):
                if st.button("USD", key="curr_opt_usd", use_container_width=True):
                    if current_currency != "USD":
                        update_profile_currency(user_id, "USD")
                        st.session_state["display_currency"] = "USD"
                        st.rerun()
                
                if st.button("PHP", key="curr_opt_php", use_container_width=True):
                    if current_currency != "PHP":
                        update_profile_currency(user_id, "PHP")
                        st.session_state["display_currency"] = "PHP"
                        st.rerun()
            
            # Ensure session state is synced with current profile currency
            st.session_state["display_currency"] = current_currency
    
        with col3:
            if user:
                st.markdown(f"<div style='text-align: right; user-select: none; padding-top: 8px;'>{user.email}</div>", unsafe_allow_html=True)
    
        with col4:
            if st.button("Logout", use_container_width=True, key="header_logout"):
                logout()
                st.rerun()


def render_main_content():
    render_header()
    render_dashboard()


def render_dashboard():
    # Spacer to push content down below fixed header
    # Removed spacer to minimize gap
    
    col1, col2, col3, col4 = st.columns([0.4, 0.2, 0.2, 0.2])
    with col1:
        st.title("Dashboard")
    with col2:
        if st.button("Upload CSV", use_container_width=True):
            open_upload_csv_modal()
    with col3:
        if st.button("Holdings", use_container_width=True):
            open_holdings_modal()
    with col4:
        if st.button("Add Transaction", type="primary", use_container_width=True):
            open_add_transaction_modal()
    
    user_id = get_current_user_id()
    currency = st.session_state.get("display_currency", "USD")
    symbol = "₱" if currency == "PHP" else "$"
    rate = get_usd_php_rate() if currency == "PHP" else 1.0

    with st.spinner("Loading data..."):
        transactions = get_transactions(user_id)
        holdings = get_holdings(user_id)
        enriched_holdings = calculate_holdings_value(holdings) if holdings else []
        portfolio_value = get_total_portfolio_value(enriched_holdings)
    
    # Process transactions for currency
    transactions_df = pd.DataFrame(transactions) if transactions else pd.DataFrame()
    if not transactions_df.empty:
        transactions_df['amount'] = transactions_df['amount'] * rate

    # Calculate KPIs with converted values
    kpis = calculate_kpis(transactions_df, portfolio_value * rate)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Net Worth", f"{symbol}{kpis['net_worth']:,.2f}")
    col2.metric("Monthly Income", f"{symbol}{kpis['monthly_income']:,.2f}")
    col3.metric("Monthly Burn Rate", f"{symbol}{kpis['burn_rate']:,.2f}")
    col4.metric("Savings Rate", f"{kpis['savings_rate']:.1f}%")
    
    st.markdown("---")
    
    if not transactions_df.empty:
        st.subheader("Cash Flow")
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
        
        # Determine date range limits
        min_date = transactions_df['date'].min().date()
        max_date = transactions_df['date'].max().date()
        
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        filtered_df = transactions_df
        if len(date_range) == 2:
            mask = (transactions_df['date'].dt.date >= date_range[0]) & \
                   (transactions_df['date'].dt.date <= date_range[1])
            filtered_df = transactions_df[mask]
        
        sankey_fig = create_sankey_diagram(filtered_df, symbol=symbol)
        st.plotly_chart(sankey_fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            trend_fig = create_spending_trend_chart(transactions_df, symbol=symbol)
            st.plotly_chart(trend_fig, use_container_width=True)
        with col2:
            category_fig = create_spending_by_category_chart(filtered_df, symbol=symbol)
            st.plotly_chart(category_fig, use_container_width=True)
    else:
        st.info("No transactions yet. Upload a CSV or add transactions manually to get started!")
    
    if enriched_holdings:
        st.markdown("---")
        st.subheader("💼 Portfolio Summary")
        
        # Convert holding values for the table
        for h in enriched_holdings:
            for key in ['current_price', 'current_value', 'cost_basis', 'gain']:
                if h.get(key):
                    h[key] = h[key] * rate

        col1, col2 = st.columns(2)
        with col1:
            holdings_fig = create_holdings_chart(enriched_holdings)
            st.plotly_chart(holdings_fig, use_container_width=True)
        with col2:
            holdings_df = pd.DataFrame(enriched_holdings)
            display_cols = ['ticker', 'quantity', 'current_price', 'current_value', 'gain_pct']
            available_cols = [c for c in display_cols if c in holdings_df.columns]
            
            if available_cols:
                st.dataframe(
                    holdings_df[available_cols].style.format({
                        'current_price': f'{symbol}{{:.2f}}', 
                        'current_value': f'{symbol}{{:.2f}}', 
                        'gain_pct': '{:+.2f}%'
                    }, na_rep='-'),
                    use_container_width=True
                )


@st.dialog("Upload Bank CSV")
def open_upload_csv_modal():
    user_id = get_current_user_id()
    
    st.markdown("""
    Supported formats:
    - **Chase** (Credit Card, Checking)
    - **Wells Fargo**
    - **Bank of America**
    - **Generic** (columns: date, description, amount)
    """)
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    account_source = st.text_input("Account Name", placeholder="e.g., Chase Sapphire")
    
    if uploaded_file is not None:
        st.subheader("Preview")
        preview_df = pd.read_csv(uploaded_file)
        st.dataframe(preview_df.head(5), use_container_width=True, height=150)
        
        uploaded_file.seek(0)
        
        if st.button("Process & Import", type="primary", use_container_width=True):
            with st.status("Importing data...", expanded=True) as status:
                st.write("Fetching existing records...")
                existing_sigs = get_existing_signatures(user_id)
                
                st.write("Parsing CSV...")
                result_df, stats = process_csv(
                    uploaded_file,
                    user_id,
                    account_source or "Unknown",
                    existing_signatures=existing_sigs
                )
                
                if result_df is not None:
                    st.write(f"Processed {stats['processed']} transactions.")
                    st.write("Saving to database...")
                    records = result_df.to_dict('records')
                    insert_transactions(records)
                    display_success = True
                    status.update(label="Import Complete!", state="complete", expanded=False)
                else:
                    display_success = False
                    status.update(label="Import Failed", state="error", expanded=True)
            
            if display_success:
                st.success(f"Successfully imported {stats['processed']} transactions!")
                
                if stats['skipped_duplicate'] > 0:
                    st.warning(f"Skipped {stats['skipped_duplicate']} duplicate transactions")
                
                if stats['skipped_invalid'] > 0:
                    st.info(f"Skipped {stats['skipped_invalid']} invalid rows")
                    
                st.balloons()
                if st.button("Close"):
                    st.rerun()
            else:
                st.error(f"Error: {stats.get('error', 'Unknown error')}")


@st.dialog("Investment Holdings", width="large")
def open_holdings_modal():
    user_id = get_current_user_id()
    
    with st.spinner("Fetching prices..."):
        holdings = get_holdings(user_id)
        enriched_holdings = calculate_holdings_value(holdings) if holdings else []
    
    with st.expander("➕ Add New Holding", expanded=not holdings):
        with st.form("add_holding_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ticker = st.text_input("Ticker Symbol", placeholder="AAPL").upper()
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
            with col3:
                avg_cost = st.number_input("Avg Cost (optional)", min_value=0.0, step=0.01)
            
            submitted = st.form_submit_button("Add Holding", use_container_width=True)
            
            if submitted:
                if not ticker:
                    st.error("Please enter a ticker symbol")
                elif quantity <= 0:
                    st.error("Quantity must be greater than 0")
                elif not validate_ticker(ticker):
                    st.error(f"Invalid ticker: {ticker}")
                else:
                    holding = {
                        "user_id": user_id,
                        "ticker": ticker,
                        "quantity": quantity,
                        "avg_cost": avg_cost if avg_cost > 0 else None
                    }
                    insert_holding(holding)
                    st.success(f"Added {quantity} shares of {ticker}")
                    st.rerun()
    
    if enriched_holdings:
        total_value = sum(h.get('current_value', 0) or 0 for h in enriched_holdings)
        total_gain = sum(h.get('gain', 0) or 0 for h in enriched_holdings)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
        col2.metric("Total Gain/Loss", f"${total_gain:+,.2f}")
        
        st.markdown("---")
        
        for holding in enriched_holdings:
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
                
                col1.write(f"**{holding['ticker']}**")
                col2.write(f"Qty: {holding['quantity']}")
                col3.write(f"Price: ${holding.get('current_price', 0):,.2f}" if holding.get('current_price') else "Price: N/A")
                col4.write(f"Value: ${holding.get('current_value', 0):,.2f}" if holding.get('current_value') else "Value: N/A")
                
                gain_pct = holding.get('gain_pct')
                if gain_pct is not None:
                    color = "green" if gain_pct >= 0 else "red"
                    col5.markdown(f":{color}[{gain_pct:+.2f}%]")
                else:
                    col5.write("-")
                
                if col6.button("🗑️", key=f"del_{holding['id']}"):
                    delete_holding(holding['id'])
                    st.rerun()
                
                st.markdown("---")
    else:
        st.info("No holdings yet. Add your first investment above!")


@st.dialog("Add Transaction")
def open_add_transaction_modal():
    user_id = get_current_user_id()
    
    with st.form("add_transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date")
            description = st.text_input("Description", placeholder="e.g., Grocery shopping")
        
        with col2:
            amount = st.number_input("Amount", step=0.01, help="Negative for expenses, positive for income")
            category = st.selectbox("Category", [
                "Uncategorized", "Housing", "Utilities", "Groceries", "Dining",
                "Transport", "Shopping", "Entertainment", "Healthcare",
                "Insurance", "Subscriptions", "Travel", "Income", "Transfer"
            ])
        
        account_source = st.text_input("Account Source", placeholder="e.g., Chase Checking")
        
        submitted = st.form_submit_button("Add Transaction", type="primary", use_container_width=True)
        
        if submitted:
            if not description:
                st.error("Please enter a description")
            elif amount == 0:
                st.error("Amount cannot be zero")
            else:
                transaction = {
                    "user_id": user_id,
                    "date": date.strftime("%Y-%m-%d"),
                    "description": description,
                    "amount": amount,
                    "category": category,
                    "account_source": account_source or "Unknown"
                }
                insert_transactions([transaction])
                st.success("Transaction added successfully!")
                st.balloons()
                st.rerun()


if __name__ == "__main__":
    main()
