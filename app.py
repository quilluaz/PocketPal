"""
Personal Finance HQ - Main Application Entry Point
"""
import streamlit as st
import pandas as pd

# Page config must be first Streamlit command
st.set_page_config(
    page_title="Personal Finance HQ",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.auth import init_session_state, is_authenticated, render_auth_page, logout, get_current_user_id
from src.db_connector import get_transactions, insert_transactions, delete_transaction, get_holdings, insert_holding, delete_holding, check_duplicate_transaction
from src.etl_pipeline import process_csv
from src.market_data import calculate_holdings_value, get_total_portfolio_value, validate_ticker
from src.visuals import create_sankey_diagram, create_spending_by_category_chart, create_spending_trend_chart, create_holdings_chart, calculate_kpis


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Check authentication
    if not is_authenticated():
        render_auth_page()
        return
    
    # Authenticated - show main app
    render_sidebar()
    render_main_content()


def render_sidebar():
    """Render the sidebar with navigation and quick actions."""
    with st.sidebar:
        st.title("🏦 Finance HQ")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigate",
            ["📊 Dashboard", "📤 Upload CSV", "💼 Holdings", "➕ Add Transaction"],
            label_visibility="collapsed"
        )
        st.session_state["current_page"] = page
        
        st.markdown("---")
        
        # User info
        user = st.session_state.get("user")
        if user:
            st.caption(f"Logged in as: {user.email}")
        
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()


def render_main_content():
    """Render the main content area based on selected page."""
    page = st.session_state.get("current_page", "📊 Dashboard")
    
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "📤 Upload CSV":
        render_upload_page()
    elif page == "💼 Holdings":
        render_holdings_page()
    elif page == "➕ Add Transaction":
        render_add_transaction_page()


def render_dashboard():
    """Render the main dashboard with KPIs and charts."""
    st.title("📊 Dashboard")
    
    user_id = get_current_user_id()
    
    # Fetch data
    with st.spinner("Loading data..."):
        transactions = get_transactions(user_id)
        holdings = get_holdings(user_id)
        enriched_holdings = calculate_holdings_value(holdings) if holdings else []
        portfolio_value = get_total_portfolio_value(enriched_holdings)
    
    # Convert to DataFrame
    transactions_df = pd.DataFrame(transactions) if transactions else pd.DataFrame()
    
    # Calculate KPIs
    kpis = calculate_kpis(transactions_df, portfolio_value)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Net Worth",
            value=f"${kpis['net_worth']:,.2f}"
        )
    
    with col2:
        st.metric(
            label="Monthly Income",
            value=f"${kpis['monthly_income']:,.2f}"
        )
    
    with col3:
        st.metric(
            label="Monthly Burn Rate",
            value=f"${kpis['burn_rate']:,.2f}"
        )
    
    with col4:
        savings_color = "normal" if kpis['savings_rate'] >= 0 else "inverse"
        st.metric(
            label="Savings Rate",
            value=f"{kpis['savings_rate']:.1f}%"
        )
    
    st.markdown("---")
    
    # Charts
    if not transactions_df.empty:
        # Sankey Diagram
        st.subheader("Cash Flow")
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            if 'date' in transactions_df.columns:
                transactions_df['date'] = pd.to_datetime(transactions_df['date'])
                min_date = transactions_df['date'].min().date()
                max_date = transactions_df['date'].max().date()
                
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(date_range) == 2:
                    mask = (transactions_df['date'].dt.date >= date_range[0]) & \
                           (transactions_df['date'].dt.date <= date_range[1])
                    filtered_df = transactions_df[mask]
                else:
                    filtered_df = transactions_df
            else:
                filtered_df = transactions_df
        
        # Display Sankey
        sankey_fig = create_sankey_diagram(filtered_df)
        st.plotly_chart(sankey_fig, use_container_width=True)
        
        # Additional charts
        col1, col2 = st.columns(2)
        
        with col1:
            trend_fig = create_spending_trend_chart(transactions_df)
            st.plotly_chart(trend_fig, use_container_width=True)
        
        with col2:
            category_fig = create_spending_by_category_chart(filtered_df)
            st.plotly_chart(category_fig, use_container_width=True)
    else:
        st.info("No transactions yet. Upload a CSV or add transactions manually to get started!")
    
    # Holdings summary
    if enriched_holdings:
        st.markdown("---")
        st.subheader("💼 Portfolio Summary")
        
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
                        'current_price': '${:,.2f}',
                        'current_value': '${:,.2f}',
                        'gain_pct': '{:+.2f}%'
                    }, na_rep='-'),
                    use_container_width=True
                )


def render_upload_page():
    """Render the CSV upload page."""
    st.title("📤 Upload Bank CSV")
    
    user_id = get_current_user_id()
    
    st.markdown("""
    Upload a CSV export from your bank. Supported formats:
    - **Chase** (Credit Card, Checking)
    - **Wells Fargo**
    - **Bank of America**
    - **Generic** (columns: date, description, amount)
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    with col2:
        account_source = st.text_input("Account Name", placeholder="e.g., Chase Sapphire")
    
    if uploaded_file is not None:
        # Preview
        st.subheader("Preview")
        preview_df = pd.read_csv(uploaded_file)
        st.dataframe(preview_df.head(10), use_container_width=True)
        
        # Reset file position
        uploaded_file.seek(0)
        
        if st.button("Process & Import", type="primary", use_container_width=True):
            with st.status("Importing data...", expanded=True) as status:
                st.write("Parsing CSV...")
                result_df, stats = process_csv(
                    uploaded_file,
                    user_id,
                    account_source or "Unknown",
                    check_duplicate=check_duplicate_transaction
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
                    
                st.dataframe(result_df, use_container_width=True)
                st.balloons()
            else:
                st.error(f"Error: {stats.get('error', 'Unknown error')}")
                if 'columns_found' in stats:
                    st.info(f"Columns found: {stats['columns_found']}")


def render_holdings_page():
    """Render the holdings management page."""
    st.title("💼 Investment Holdings")
    
    user_id = get_current_user_id()
    
    # Fetch holdings
    with st.spinner("Fetching prices..."):
        holdings = get_holdings(user_id)
        enriched_holdings = calculate_holdings_value(holdings) if holdings else []
    
    # Add new holding form
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
    
    # Display holdings
    if enriched_holdings:
        # Summary metrics
        total_value = sum(h.get('current_value', 0) or 0 for h in enriched_holdings)
        total_gain = sum(h.get('gain', 0) or 0 for h in enriched_holdings)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
        col2.metric("Total Gain/Loss", f"${total_gain:+,.2f}")
        
        st.markdown("---")
        
        # Holdings table with delete buttons
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


def render_add_transaction_page():
    """Render the manual transaction entry page."""
    st.title("➕ Add Transaction")
    
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
    
    # Recent transactions
    st.markdown("---")
    st.subheader("Recent Transactions")
    
    transactions = get_transactions(user_id, limit=20)
    
    if transactions:
        for txn in transactions:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
                
                col1.write(txn['date'])
                col2.write(txn['description'][:40] + "..." if len(txn['description']) > 40 else txn['description'])
                
                amount = txn['amount']
                color = "green" if amount > 0 else "red"
                col3.markdown(f":{color}[${abs(amount):,.2f}]")
                
                col4.write(txn['category'])
                
                if col5.button("🗑️", key=f"del_txn_{txn['id']}"):
                    delete_transaction(txn['id'])
                    st.rerun()
    else:
        st.info("No transactions yet.")


if __name__ == "__main__":
    main()
