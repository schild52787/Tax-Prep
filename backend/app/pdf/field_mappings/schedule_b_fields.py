"""Field mapping for Schedule B - Interest and Ordinary Dividends.

Schedule B has repeating rows for payer names and amounts.
We map the first 14 interest payers and 16 dividend payers.
"""

SCHEDULE_B_FIELDS = {
    # Header
    "taxpayer.name": "f1_01[0]",
    "taxpayer.ssn": "f1_02[0]",

    # Part I - Interest (payer name / amount pairs)
    "interest_payer_1": "f1_03[0]",
    "interest_amount_1": "f1_04[0]",
    "interest_payer_2": "f1_05[0]",
    "interest_amount_2": "f1_06[0]",
    "interest_payer_3": "f1_07[0]",
    "interest_amount_3": "f1_08[0]",
    "interest_payer_4": "f1_09[0]",
    "interest_amount_4": "f1_10[0]",
    "interest_payer_5": "f1_11[0]",
    "interest_amount_5": "f1_12[0]",
    "interest_payer_6": "f1_13[0]",
    "interest_amount_6": "f1_14[0]",
    "interest_payer_7": "f1_15[0]",
    "interest_amount_7": "f1_16[0]",
    "interest_payer_8": "f1_17[0]",
    "interest_amount_8": "f1_18[0]",
    "interest_payer_9": "f1_19[0]",
    "interest_amount_9": "f1_20[0]",
    "interest_payer_10": "f1_21[0]",
    "interest_amount_10": "f1_22[0]",
    "interest_payer_11": "f1_23[0]",
    "interest_amount_11": "f1_24[0]",
    "interest_payer_12": "f1_25[0]",
    "interest_amount_12": "f1_26[0]",
    "interest_payer_13": "f1_27[0]",
    "interest_amount_13": "f1_28[0]",
    "interest_payer_14": "f1_29[0]",
    "interest_amount_14": "f1_30[0]",
    "line_4": "f1_31[0]",         # Total Part I interest

    # Part II - Ordinary Dividends
    "dividend_payer_1": "f1_32[0]",
    "dividend_amount_1": "f1_33[0]",
    "dividend_payer_2": "f1_34[0]",
    "dividend_amount_2": "f1_35[0]",
    "dividend_payer_3": "f1_36[0]",
    "dividend_amount_3": "f1_37[0]",
    "dividend_payer_4": "f1_38[0]",
    "dividend_amount_4": "f1_39[0]",
    "dividend_payer_5": "f1_40[0]",
    "dividend_amount_5": "f1_41[0]",
    "dividend_payer_6": "f1_42[0]",
    "dividend_amount_6": "f1_43[0]",
    "dividend_payer_7": "f1_44[0]",
    "dividend_amount_7": "f1_45[0]",
    "dividend_payer_8": "f1_46[0]",
    "dividend_amount_8": "f1_47[0]",
    "dividend_payer_9": "f1_48[0]",
    "dividend_amount_9": "f1_49[0]",
    "dividend_payer_10": "f1_50[0]",
    "dividend_amount_10": "f1_51[0]",
    "dividend_payer_11": "f1_52[0]",
    "dividend_amount_11": "f1_53[0]",
    "dividend_payer_12": "f1_54[0]",
    "dividend_amount_12": "f1_55[0]",
    "dividend_payer_13": "f1_56[0]",
    "dividend_amount_13": "f1_57[0]",
    "dividend_payer_14": "f1_58[0]",
    "dividend_amount_14": "f1_59[0]",
    "dividend_payer_15": "f1_60[0]",
    "dividend_amount_15": "f1_61[0]",
    "dividend_payer_16": "f1_62[0]",
    "dividend_amount_16": "f1_63[0]",
    "line_6": "f1_64[0]",         # Total Part II dividends
}
