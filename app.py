
import streamlit as st
import pandas as pd
import re

def clean_phone_numbers(text):
    if pd.isna(text):
        return []

    text = str(text)
    text = text.replace('o', '0').replace('O', '0')  # fix letter o
    text = text.replace('|', ' ').replace('-', ' ').replace('/', ' ')
    text = re.sub(r'[^\d+,\s\(\)\^&]', ' ', text)
    parts = re.split(r'[,\s;/|()\^&]+', text)

    results = set()
    for part in parts:
        digits = re.sub(r'\D', '', part)

        # Mobile with country code
        if digits.startswith('00971') and len(digits) == 14 and digits[5] == '5':
            results.add('+971' + digits[5:])
        elif digits.startswith('971') and len(digits) == 12 and digits[3] == '5':
            results.add('+971' + digits[3:])
        elif digits.startswith('05') and len(digits) == 10:
            results.add('+971' + digits[1:])
        elif digits.startswith('5') and len(digits) == 9:
            results.add('+971' + digits)

        # Landline
        elif digits.startswith('00971') and digits[5] in '23467' and len(digits) == 12:
            results.add('+971' + digits[5:])
        elif digits.startswith('971') and digits[3] in '23467' and len(digits) == 11:
            results.add('+971' + digits[3:])
        elif digits.startswith('0') and digits[1] in '23467' and len(digits) == 9:
            results.add('+971' + digits[1:])
        elif digits.startswith('2') or digits.startswith('3') or digits.startswith('4'):
            if len(digits) == 7:
                results.add('+971' + digits)

    return list(results)

def process_file(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    all_numbers = set()

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        for column in df.columns:
            for cell in df[column]:
                numbers = clean_phone_numbers(cell)
                all_numbers.update(numbers)

    output_df = pd.DataFrame(sorted(all_numbers), columns=["Cleaned UAE Numbers"])
    return output_df

st.title("🇦🇪 UAE Phone Cleaner V2.2")

uploaded_file = st.file_uploader("Upload messy Excel file", type=["xlsx"])

if uploaded_file:
    cleaned_df = process_file(uploaded_file)
    st.success(f"✅ Found {len(cleaned_df)} unique phone numbers.")
    st.dataframe(cleaned_df)

    cleaned_file = "uae_cleaned_output.xlsx"
    cleaned_df.to_excel(cleaned_file, index=False)
    with open(cleaned_file, "rb") as f:
        st.download_button("📥 Download Cleaned File", f, file_name=cleaned_file)
