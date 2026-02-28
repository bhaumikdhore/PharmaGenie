import pandas as pd

inventory = pd.read_csv("data/inventory.csv")

def calculate_tax(bill_details):
    total_tax = 0

    for item in bill_details:
        row = inventory[inventory["name"] == item["name"]]
        tax_percent = float(row["tax_percent"].values[0])

        tax_amount = item["total_price"] * (tax_percent / 100)
        total_tax += tax_amount

    return round(total_tax, 2)