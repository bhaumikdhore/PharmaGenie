import pandas as pd

def log_transaction(invoice):
    try:
        transactions = pd.read_csv("data/transactions.csv")
    except:
        transactions = pd.DataFrame(columns=["invoice_id", "total"])

    new_row = {
        "invoice_id": invoice["invoice_id"],
        "total": invoice["total"]
    }

    transactions = pd.concat([transactions, pd.DataFrame([new_row])])
    transactions.to_csv("data/transactions.csv", index=False)