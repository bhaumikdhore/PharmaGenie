from rapidfuzz import fuzz
import pandas as pd

med_db = pd.read_csv("data/medicine_master.csv")

def match_medicines(prescribed_list):

    matched = []
    unmatched = []

    for p in prescribed_list:

        med_name = p["name"]   # <-- FIX HERE

        best_match = None
        highest_score = 0

        for med in med_db["name"]:
            score = fuzz.ratio(med_name.lower(), med.lower())
            if score > highest_score:
                highest_score = score
                best_match = med

        if highest_score > 80:
            matched.append(best_match)
        else:
            unmatched.append(med_name)

    return matched, unmatched