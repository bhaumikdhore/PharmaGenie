import pandas as pd

inventory = pd.read_csv("data/inventory.csv")

def calculate_prices(cart_items):
    bill_details = []
    subtotal = 0

    for item in cart_items:
        row = inventory[inventory["name"] == item["name"]]

        if row.empty:
            continue

        price = float(row["price"].values[0])
        quantity = item["quantity"]

        total_price = price * quantity
        subtotal += total_price

        bill_details.append({
            "name": item["name"],
            "quantity": quantity,
            "unit_price": price,
            "total_price": total_price
        })

    return bill_details, subtotal