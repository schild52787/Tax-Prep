"""Field mapping for Schedule A - Itemized Deductions."""

SCHEDULE_A_FIELDS = {
    # Header
    "taxpayer.name": "f1_1[0]",
    "taxpayer.ssn": "f1_2[0]",

    # Medical and Dental Expenses
    "line_1": "f1_3[0]",       # Medical and dental expenses
    "line_2": "f1_4[0]",       # AGI from Form 1040, line 11
    "line_3": "f1_5[0]",       # 7.5% of line 2
    "line_4": "f1_6[0]",       # Subtract line 3 from line 1

    # Taxes You Paid
    "line_5a": "f1_7[0]",      # State and local income taxes
    "line_5b": "f1_8[0]",      # State and local sales taxes
    "line_5c": "f1_9[0]",      # Personal property taxes
    "line_5d": "f1_10[0]",     # Add lines 5a through 5c
    "line_5e": "f1_11[0]",     # SALT cap applied
    "line_6": "f1_12[0]",      # Other taxes
    "line_7": "f1_13[0]",      # Total taxes paid

    # Interest You Paid
    "line_8a": "f1_14[0]",     # Home mortgage interest (1098)
    "line_8b": "f1_16[0]",     # Home mortgage interest (not 1098)
    "line_8c": "f1_17[0]",     # Points not reported on 1098
    "line_9": "f1_18[0]",      # Investment interest
    "line_10": "f1_19[0]",     # Total interest

    # Gifts to Charity
    "line_11": "f1_20[0]",     # Gifts by cash or check
    "line_12": "f1_21[0]",     # Other than cash or check
    "line_13": "f1_22[0]",     # Carryover from prior year
    "line_14": "f1_23[0]",     # Total gifts to charity

    # Casualty and Theft Losses
    "line_15": "f1_24[0]",     # Casualty and theft losses

    # Other Itemized Deductions
    "line_16": "f1_25[0]",     # Other itemized deductions

    # Total
    "line_17": "f1_26[0]",     # Total itemized deductions
}
