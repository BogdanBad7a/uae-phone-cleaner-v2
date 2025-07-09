import streamlit as st
import pandas as pd
import re
import io

# Streamlit app: UAE Phone Cleaner v2.2 (handles 27 manual cases)

st.set_page_config(page_title="UAE Phone Cleaner v2.2", layout="centered")
st.title("📞 UAE Phone Number Cleaner v2.2")

# Delimiters and patterns
DELIMITER_SPLIT = r'[|/\\,;+&\^\(\)\s]+'
AND_PATTERN = re.compile(r'\bAND\b', flags=re.IGNORECASE)
EXT_FAX_PATTERN = re.compile(r'(?:ext|fax)\d+', flags=re.IGNORECASE)

# Extract numbers from a single text cell
def extract_from_text(text: str) -> set[str]:
    phones = set()
    # 1. Normalize AND and custom separators
    text = AND_PATTERN.sub(' ', text)
    text = text.replace('^^', ' ')

    # 2. Split on delimiters
    tokens = re.split(DELIMITER_SPLIT, text)
    cleaned = []
    for tok in tokens:
        tok = tok.strip().lower().replace('o', '0').replace('a', '0')
        # strip leading punctuation
        tok = re.sub(r'^[",]+', '', tok)
        # remove extensions and fax labels
        tok = EXT_FAX_PATTERN.sub('', tok)
        # skip scientific notation
        if re.search(r'[eE]\+', tok):
            continue
        # extract digits only
        digits = re.sub(r'\D', '', tok)
        if not digits:
            continue
        cleaned.append(digits)

    # 3. Direct classification
    for digits in cleaned:
        # strip leading zeros if double/triple
        if digits.startswith('00'):
            # Case 9: replace leading 00+ with nothing
            digits = digits.lstrip('0')
        # Case 6: remove stray 0 after country code
        if digits.startswith('9710'):
            digits = digits[:3] + digits[4:]
        # classify mobile/int'l mobile
        if re.fullmatch(r'9715\d{8}', digits):
            phones.add('+' + digits)
            continue
        if re.fullmatch(r'5\d{8}', digits):
            phones.add('+971' + digits)
            continue
        if re.fullmatch(r'05\d{8}', digits):
            phones.add('+971' + digits[1:])
            continue
        # classify landline (area codes 2,3,4,6)
        if re.fullmatch(r'971[2346]\d{7}', digits):
            phones.add('+' + digits)
            continue
        if re.fullmatch(r'[2346]\d{7}', digits):
            phones.add('+971' + digits)
            continue
        if re.fullmatch(r'0[2346]\d{7}', digits):
            phones.add('+971' + digits[1:])
            continue

    # 4. Handle reversed prefix-body combinations (Cases 2,3,5)
    # identify potential prefixes and bodies
    prefix_mobile = [d for d in cleaned if re.fullmatch(r'0?5\d', d)]
    prefix_land   = [d for d in cleaned if re.fullmatch(r'0?[2346]', d)]
    body_tokens   = [d for d in cleaned if re.fullmatch(r'\d{7}', d)]

    for prefix in prefix_mobile:
        # normalize mobile prefix to two digits
        if len(prefix) == 3 and prefix.startswith('0'):
            mp = prefix[1:]
        else:
            mp = prefix
        for body in body_tokens:
            comb = mp + body
            if re.fullmatch(r'5\d{8}', comb):
                phones.add('+971' + comb)

    for prefix in prefix_land:
        # normalize landline area code to one digit
        if len(prefix) == 2 and prefix.startswith('0'):
            ap = prefix[1]
        else:
            ap = prefix[-1]
        for body in body_tokens:
            comb = ap + body
            if re.fullmatch(r'[2346]\d{7}', comb):
                phones.add('+971' + comb)

    return phones

# Extract from entire DataFrame
def extract_phones(df: pd.DataFrame) -> set[str]:
    result = set()
    for col in df.columns:
        for val in df[col].dropna():
            text = str(val)
            result |= extract_from_text(text)
    return result

# Streamlit UI
uploaded = st.file_uploader("Upload Excel File (.xlsx)", type=['xlsx'])
if uploaded:
    df_all = pd.read_excel(uploaded, sheet_name=None)
    all_numbers = set()
    for sheet, df in df_all.items():
        all_numbers |= extract_phones(df)

    unique_numbers = sorted(all_numbers)
    final_df = pd.DataFrame({"Cleaned Phone Number": unique_numbers})

    st.success(f"✅ Found {len(final_df)} valid UAE numbers.")
    st.dataframe(final_df)

    # Downloadable Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False)
    st.download_button("📥 Download Cleaned Excel", output.getvalue(), file_name="cleaned_uae_numbers_v2.xlsx")
