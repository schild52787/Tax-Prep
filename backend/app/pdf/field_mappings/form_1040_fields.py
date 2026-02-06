"""Field mapping for Form 1040 - U.S. Individual Income Tax Return.

Maps our calculation result keys to IRS PDF field names discovered
via inspect_pdf_fields.py.

Field naming convention:
  f1_XX[0] = text field on page 1 (sequential numbering)
  f2_XX[0] = text field on page 2
  c1_X[0]  = checkbox on page 1
  c2_X[0]  = checkbox on page 2
"""

FORM_1040_FIELDS = {
    # === PAGE 1 HEADER ===
    "taxpayer.first_name_mi": "f1_11[0]",       # Your first name and middle initial
    "taxpayer.last_name": "f1_12[0]",            # Your last name
    "taxpayer.ssn": "f1_16[0]",                  # Your SSN (9 chars)
    "spouse.first_name_mi": "f1_13[0]",          # Spouse first name and MI
    "spouse.last_name": "f1_14[0]",              # Spouse last name
    "spouse.ssn": "f1_19[0]",                    # Spouse SSN
    "address.street": "f1_17[0]",                # Home address
    "address.apt": "f1_18[0]",                   # Apt no.
    "address.city_state_zip": "f1_20[0]",        # City, state, ZIP

    # === FILING STATUS CHECKBOXES ===
    "filing_status.single": "c1_1[0]",           # Single
    "filing_status.mfj": "c1_2[0]",              # Married Filing Jointly

    # === INCOME ===
    "line_1a": "f1_31[0]",      # Wages, salaries, tips
    "line_1z": "f1_38[0]",      # Total from adding lines 1a through 1h
    "line_2a": "f1_47[0]",      # Tax-exempt interest
    "line_2b": "f1_48[0]",      # Taxable interest
    "line_3a": "f1_49[0]",      # Qualified dividends
    "line_3b": "f1_50[0]",      # Ordinary dividends
    "line_4a": "f1_51[0]",      # IRA distributions
    "line_4b": "f1_52[0]",      # IRA taxable amount
    "line_5a": "f1_53[0]",      # Pensions and annuities
    "line_5b": "f1_54[0]",      # Pensions taxable amount
    "line_6a": "f1_55[0]",      # Social Security benefits
    "line_6b": "f1_56[0]",      # SS taxable amount
    "line_7": "f1_57[0]",       # Capital gain or loss
    "line_8": "f1_58[0]",       # Other income from Schedule 1
    "line_9": "f1_59[0]",       # Total income

    # === ADJUSTMENTS ===
    "line_10": "f1_60[0]",      # Adjustments from Schedule 1
    "line_11": "f1_61[0]",      # Adjusted Gross Income

    # === PAGE 2 - DEDUCTIONS & TAX ===
    "line_12": "f2_02[0]",      # Standard/itemized deduction
    "line_13": "f2_03[0]",      # QBI deduction
    "line_14": "f2_04[0]",      # Total deductions
    "line_15": "f2_05[0]",      # Taxable income
    "line_16": "f2_06[0]",      # Tax
    "line_17": "f2_07[0]",      # Additional taxes from Schedule 2
    "line_18": "f2_08[0]",      # Total (lines 16+17)
    "line_19": "f2_09[0]",      # Child tax credit
    "line_20": "f2_10[0]",      # Total credits
    "line_21": "f2_11[0]",      # Tax after credits
    "line_22": "f2_12[0]",      # Other taxes from Schedule 2
    "line_23": "f2_13[0]",      # Total tax
    "line_24": "f2_14[0]",      # Total tax (same as 23)

    # === PAYMENTS ===
    "line_25a": "f2_15[0]",     # W-2 withholding
    "line_25b": "f2_16[0]",     # 1099 withholding
    "line_25c": "f2_17[0]",     # Other withholding
    "line_25d": "f2_18[0]",     # Total withholding
    "line_26": "f2_19[0]",      # Estimated tax payments
    "line_27": "f2_24[0]",      # Earned income credit
    "line_28": "f2_25[0]",      # Additional child tax credit
    "line_29": "f2_26[0]",      # American opportunity credit
    "line_33": "f2_30[0]",      # Total payments

    # === REFUND / AMOUNT OWED ===
    "line_34": "f2_31[0]",      # Overpayment
    "line_35a": "f2_34[0]",     # Refund amount
    "line_37": "f2_37[0]",      # Amount owed
}
