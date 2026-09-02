from parser_v3 import load_and_clean_all_sheets

df = load_and_clean_all_sheets()

for name in sorted(df["NAME"].unique()):
    print(name)