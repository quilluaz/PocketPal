"""
ETL Pipeline for processing bank CSV exports.
Handles detection, parsing, cleaning, and categorization.
"""
import pandas as pd
import re
from datetime import datetime
from typing import Callable


# ============================================================
# BANK FORMAT DETECTION
# ============================================================

BANK_FORMATS = {
    "chase": {
        "identifiers": ["Posting Date", "Details", "Amount"],
        "date_col": "Posting Date",
        "description_col": "Description",
        "amount_col": "Amount",
        "date_format": "%m/%d/%Y"
    },
    "wells_fargo": {
        "identifiers": ["Date", "Amount", "Running Bal."],
        "date_col": "Date",
        "description_col": "Description",
        "amount_col": "Amount",
        "date_format": "%m/%d/%Y"
    },
    "bank_of_america": {
        "identifiers": ["Posted Date", "Reference Number", "Payee"],
        "date_col": "Posted Date",
        "description_col": "Payee",
        "amount_col": "Amount",
        "date_format": "%m/%d/%Y"
    },
    "generic": {
        "identifiers": ["date", "description", "amount"],
        "date_col": "date",
        "description_col": "description",
        "amount_col": "amount",
        "date_format": "%Y-%m-%d"
    }
}


def detect_bank_format(df: pd.DataFrame) -> str:
    """
    Detect which bank format the CSV uses based on column headers.
    Returns the bank format key or 'unknown'.
    """
    columns_lower = [col.lower() for col in df.columns]
    
    for bank, config in BANK_FORMATS.items():
        identifiers = [id.lower() for id in config["identifiers"]]
        if all(any(id in col for col in columns_lower) for id in identifiers):
            return bank
    
    return "unknown"


def get_column_mapping(df: pd.DataFrame, bank_format: str) -> dict:
    """
    Get the column name mapping for a specific bank format.
    Handles case-insensitive matching.
    """
    if bank_format not in BANK_FORMATS:
        return {}
    
    config = BANK_FORMATS[bank_format]
    mapping = {}
    
    for col in df.columns:
        col_lower = col.lower()
        if config["date_col"].lower() in col_lower:
            mapping["date"] = col
        elif config["description_col"].lower() in col_lower:
            mapping["description"] = col
        elif config["amount_col"].lower() in col_lower:
            mapping["amount"] = col
    
    mapping["date_format"] = config["date_format"]
    return mapping


# ============================================================
# DATA CLEANING
# ============================================================

def clean_amount(value) -> float:
    """
    Clean and parse an amount value.
    Handles: $1,234.56, (500.00), -500, etc.
    """
    if pd.isna(value):
        return 0.0
    
    # Convert to string
    amount_str = str(value).strip()
    
    # Handle parentheses as negative (accounting format)
    is_negative = amount_str.startswith("(") and amount_str.endswith(")")
    if is_negative:
        amount_str = amount_str[1:-1]
    
    # Remove currency symbols and commas
    amount_str = re.sub(r'[$,]', '', amount_str)
    
    # Handle explicit negative sign
    if amount_str.startswith("-"):
        is_negative = True
        amount_str = amount_str[1:]
    
    try:
        amount = float(amount_str)
        return -amount if is_negative else amount
    except ValueError:
        return 0.0


def parse_date(value, date_format: str = "%m/%d/%Y") -> str:
    """
    Parse a date value and return as YYYY-MM-DD string.
    """
    if pd.isna(value):
        return None
    
    date_str = str(value).strip()
    
    # Try the specified format first
    formats_to_try = [date_format, "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y"]
    
    for fmt in formats_to_try:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None


# ============================================================
# AUTO-CATEGORIZATION
# ============================================================

CATEGORY_KEYWORDS = {
    "Housing": ["rent", "mortgage", "property tax", "hoa"],
    "Utilities": ["electric", "water", "gas", "internet", "comcast", "verizon", "att ", "t-mobile"],
    "Groceries": ["whole foods", "trader joe", "safeway", "kroger", "costco", "walmart", "target", "grocery", "albertsons"],
    "Dining": ["restaurant", "doordash", "uber eats", "grubhub", "mcdonald", "starbucks", "chipotle", "panera"],
    "Transport": ["uber", "lyft", "gas station", "shell", "chevron", "parking", "transit", "metro"],
    "Shopping": ["amazon", "ebay", "apple.com", "best buy", "nordstrom", "macys"],
    "Entertainment": ["netflix", "spotify", "hulu", "disney+", "hbo", "movie", "theater", "concert"],
    "Healthcare": ["pharmacy", "cvs", "walgreens", "doctor", "hospital", "medical", "dental", "vision"],
    "Insurance": ["insurance", "geico", "allstate", "progressive", "state farm"],
    "Subscriptions": ["subscription", "membership", "gym", "fitness"],
    "Travel": ["airline", "hotel", "airbnb", "booking.com", "expedia", "flight"],
    "Income": ["payroll", "direct deposit", "salary", "wage", "dividend", "interest income"],
    "Transfer": ["transfer", "zelle", "venmo", "paypal", "cash app"],
}


def categorize_transaction(description: str) -> str:
    """
    Auto-categorize a transaction based on description keywords.
    Returns category string or 'Uncategorized'.
    """
    if not description:
        return "Uncategorized"
    
    desc_lower = description.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in desc_lower for keyword in keywords):
            return category
    
    return "Uncategorized"


# ============================================================
# MAIN ETL FUNCTION
# ============================================================

def process_csv(
    file,
    user_id: str,
    account_source: str = "Unknown",
    check_duplicate: Callable = None
) -> tuple[pd.DataFrame, dict]:
    """
    Process a bank CSV file.
    
    Args:
        file: Uploaded file object
        user_id: Current user's ID
        account_source: Name of the account (e.g., "Chase Sapphire")
        check_duplicate: Optional function to check for duplicates
    
    Returns:
        (processed_df, stats_dict)
    """
    # Read CSV
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return None, {"error": f"Failed to read CSV: {str(e)}"}
    
    if df.empty:
        return None, {"error": "CSV file is empty"}
    
    # Detect bank format
    bank_format = detect_bank_format(df)
    if bank_format == "unknown":
        return None, {
            "error": "Unable to detect bank format. Expected columns: date, description, amount",
            "columns_found": list(df.columns)
        }
    
    # Get column mapping
    mapping = get_column_mapping(df, bank_format)
    if not all(k in mapping for k in ["date", "description", "amount"]):
        return None, {
            "error": f"Missing required columns for {bank_format} format",
            "mapping": mapping
        }
    
    # Process rows
    processed_rows = []
    stats = {
        "total_rows": len(df),
        "processed": 0,
        "skipped_invalid": 0,
        "skipped_duplicate": 0,
        "bank_format": bank_format
    }
    
    for _, row in df.iterrows():
        # Parse date
        date = parse_date(row[mapping["date"]], mapping["date_format"])
        if not date:
            stats["skipped_invalid"] += 1
            continue
        
        # Clean amount
        amount = clean_amount(row[mapping["amount"]])
        if amount == 0:
            stats["skipped_invalid"] += 1
            continue
        
        # Get description
        description = str(row[mapping["description"]]).strip() if pd.notna(row[mapping["description"]]) else ""
        
        # Check for duplicates
        if check_duplicate and check_duplicate(user_id, date, amount, description):
            stats["skipped_duplicate"] += 1
            continue
        
        # Auto-categorize
        category = categorize_transaction(description)
        
        # Build transaction record
        processed_rows.append({
            "user_id": user_id,
            "date": date,
            "description": description,
            "amount": amount,
            "category": category,
            "account_source": account_source
        })
        stats["processed"] += 1
    
    if not processed_rows:
        return None, {**stats, "error": "No valid transactions found after processing"}
    
    result_df = pd.DataFrame(processed_rows)
    return result_df, stats
