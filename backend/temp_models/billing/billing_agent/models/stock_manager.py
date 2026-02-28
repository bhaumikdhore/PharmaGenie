import pandas as pd

def deduct_stock(cart_items):
    inventory = pd.read_csv("data/inventory.csv")

    for item in cart_items:
        index = inventory[inventory["name"] == item["name"]].index

        if not index.empty:
            inventory.loc[index, "stock"] -= item["quantity"]

    inventory.to_csv("data/inventory.csv", index=False)