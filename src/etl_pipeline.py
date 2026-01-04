"""
ETL Pipeline for processing bank CSV exports.
Handles detection, parsing, cleaning, and categorization.
"""
import pandas as pd
import re
from datetime import datetime


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

# ============================================================
# DATA CLEANING
# ============================================================

def clean_amount_vectorized(series: pd.Series) -> pd.Series:
    """
    Clean and parse a series of amount values using vectorized string operations.
    Handles: $1,234.56, (500.00), -500, etc.
    """
    # Convert to string and strip whitespace
    s = series.astype(str).str.strip()
    
    # Identify negative values (parentheses or leading minus)
    is_negative_paren = s.str.startswith("(") & s.str.endswith(")")
    is_negative_sign = s.str.startswith("-")
    is_negative = is_negative_paren | is_negative_sign
    
    # Remove non-numeric characters (except decimal point)
    # regex matches anything that is NOT a digit or a dot
    s_clean = s.str.replace(r'[^\d.]', '', regex=True)
    
    # Convert to float (coerce errors to NaN, then fill with 0)
    amounts = pd.to_numeric(s_clean, errors='coerce').fillna(0.0)
    
    # Apply sign
    return amounts.where(~is_negative, -amounts)


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
    if not isinstance(description, str) or not description:
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
    existing_signatures: set = None
) -> tuple[pd.DataFrame | None, dict]:
    """
    Process a bank CSV file using vectorized operations.
    
    Args:
        existing_signatures: Optional set of (date, amount, description) tuples for O(1) dedup
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
    cols_needed = ["date", "description", "amount"]
    if not all(k in mapping for k in cols_needed):
        return None, {
            "error": f"Missing required columns for {bank_format} format",
            "mapping": mapping
        }

    stats = {
        "total_rows": len(df),
        "processed": 0,
        "skipped_invalid": 0,
        "skipped_duplicate": 0,
        "bank_format": bank_format
    }
    
    # 1. Vectorized Date Parsing
    df['parsed_date'] = pd.to_datetime(df[mapping['date']], errors='coerce')
    
    # 2. Vectorized Amount Cleaning
    df['parsed_amount'] = clean_amount_vectorized(df[mapping['amount']])
    
    # 3. Filter invalid rows
    valid_mask = (df['parsed_date'].notna()) & (df['parsed_amount'] != 0)
    invalid_count = (~valid_mask).sum()
    stats["skipped_invalid"] = int(invalid_count)
    
    df_clean = df[valid_mask].copy()
    
    if df_clean.empty:
        return None, {**stats, "error": "No valid transactions found after processing"}

    # 4. Prepare Description
    df_clean['clean_description'] = df_clean[mapping['description']].fillna("").astype(str).str.strip()
    
    # 5. Build final rows with O(1) deduplication
    final_rows = []
    
    for _, row in df_clean.iterrows():
        date_str = row['parsed_date'].strftime("%Y-%m-%d")
        amount = float(row['parsed_amount'])
        desc = row['clean_description']
        
        # O(1) duplicate check against pre-fetched signatures
        if existing_signatures and (date_str, amount, desc) in existing_signatures:
            stats["skipped_duplicate"] += 1
            continue
            
        # 6. Auto-Categorize (row-by-row is acceptable here as keyword search is efficient enough)
        category = categorize_transaction(desc)
        
        final_rows.append({
            "user_id": user_id,
            "date": date_str,
            "description": desc,
            "amount": amount,
            "category": category,
            "account_source": account_source
        })
        stats["processed"] += 1

    if not final_rows:
        return None, {**stats, "error": "No valid transactions found after deduplication"}
        
    return pd.DataFrame(final_rows), stats
