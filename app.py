import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="UAE Phone Cleaner V2.1", layout="centered")
st.title("📞 UAE Phone Number Cleaner - V2.1")

# Regex patterns
MOBILE_PATTERN = re.compile(r'(?:\+?971|00971|971)?[\s\-\|\/]?(5[0-9]{1})[\s\-\|\/]?([0-9]{6,7})')
LANDLINE_PATTERN = re.compile(r'(?:\+?971|00971|971)?[\s\-\|\/]?(\d{1,2})[\s\-\|\/]?(\d{6,7})')

def extract_numbers(text):
    text = str(text)  # Convert everything to string

    text = text.replace('o', '0').replace('O', '0')
    text = re.sub(r'[a-zA-Z]', '', text)
    text = re.sub(r'[\(\)\[\]{}]', ' ', text)
    text = re.sub(r'ext\d+', '', text)
    text = re.sub(r'\+1-\(\d+\)[\d\-]+', '', text)
    text = re.sub(r'[\^]', ' ', text)

    parts = re.split(r'[\s,;|/]+', text)

    # Handle suffix chaining like 23636711/16/17
    expanded = []
    for p in parts:
        if re.search(r'/\d+/?\d*', p):
            base = re.findall(r'(\d+)', p)
            if len(base) >= 2:
                root = base[0][:-2]
                suffixes = base[1:]
                for s in suffixes:
                    if len(s) == 2:
                        expanded.append(root + s)
            else:
                expanded.append(p)
        else:
            expanded.append(p)
    parts = expanded

    results = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        m = re.match(MOBILE_PATTERN, part)
        if m:
            full = '+971' + m.group(1) + m.group(2)
            if len(full) == 13:
                results.append(full)
            continue

        l = re.match(LANDLINE_PATTERN, part)
        if l:
            area = l.group(1)
            line = l.group(2)
            if area.startswith('0'):
                area = area[1:]
            results.append(f"0{area}-{line}")

    return results

def clean_excel(file):
    xl = pd.read_excel(file, sheet_name=None)
    final_numbers = set()

    for sheet, df in xl.items():
        for col in df.columns:
            for val in df[col]:
                final_numbers.update(extract_numbers(val))

    return sorted(final_numbers)

def generate_download(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output

uploaded = st.file_uploader("Upload your messy Excel file (.xlsx):", type=["xlsx"])

if uploaded:
    with st.spinner("Cleaning numbers... Hang tight!"):
        numbers = clean_excel(uploaded)
        df_cleaned = pd.DataFrame({"Cleaned Numbers": numbers})
        buffer = generate_download(df_cleaned)

    st.success(f"✅ Extracted {len(numbers)} unique numbers!")
    st.download_button("📥 Download Cleaned Excel", buffer, file_name="cleaned_numbers_v2.1.xlsx")
