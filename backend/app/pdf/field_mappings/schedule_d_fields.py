"""Field mapping for Schedule D - Capital Gains and Losses."""

SCHEDULE_D_FIELDS = {
    # Header
    "taxpayer.name": "f1_1[0]",
    "taxpayer.ssn": "f1_2[0]",

    # Part I - Short-Term Capital Gains and Losses
    "line_1a_proceeds": "f1_3[0]",    # 8949 Box A proceeds
    "line_1a_basis": "f1_4[0]",       # 8949 Box A basis
    "line_1a_adjustments": "f1_5[0]", # 8949 Box A adjustments
    "line_1a_gain": "f1_6[0]",        # 8949 Box A gain/loss
    "line_2_proceeds": "f1_7[0]",     # 8949 Box B proceeds
    "line_2_basis": "f1_8[0]",
    "line_2_adjustments": "f1_9[0]",
    "line_2_gain": "f1_10[0]",
    "line_3_proceeds": "f1_11[0]",    # 8949 Box C proceeds
    "line_3_basis": "f1_12[0]",
    "line_3_adjustments": "f1_13[0]",
    "line_3_gain": "f1_14[0]",
    "line_4": "f1_15[0]",             # Short-term gain/loss from other forms
    "line_5": "f1_16[0]",             # Net short-term from Sch D line 4/etc
    "line_6": "f1_17[0]",             # Short-term carryover
    "line_7": "f1_18[0]",             # Net short-term capital gain/loss

    # Part II - Long-Term Capital Gains and Losses
    "line_8a_proceeds": "f1_19[0]",   # 8949 Box D proceeds
    "line_8a_basis": "f1_20[0]",
    "line_8a_adjustments": "f1_21[0]",
    "line_8a_gain": "f1_22[0]",
    "line_9_proceeds": "f1_23[0]",    # 8949 Box E
    "line_9_basis": "f1_24[0]",
    "line_9_adjustments": "f1_25[0]",
    "line_9_gain": "f1_26[0]",
    "line_10_proceeds": "f1_27[0]",   # 8949 Box F
    "line_10_basis": "f1_28[0]",
    "line_10_adjustments": "f1_29[0]",
    "line_10_gain": "f1_30[0]",
    "line_11": "f1_31[0]",            # LT gain/loss from other forms
    "line_12": "f1_32[0]",            # Net LT from Sch D
    "line_13": "f1_33[0]",            # Capital gain distributions
    "line_14": "f1_34[0]",            # LT carryover
    "line_15": "f1_35[0]",            # Net long-term capital gain/loss

    # Part III - Summary
    "line_16": "f1_36[0]",            # Combine lines 7 and 15
    "line_21": "f1_43[0]",            # Net capital gain/loss (to 1040 line 7)
}
