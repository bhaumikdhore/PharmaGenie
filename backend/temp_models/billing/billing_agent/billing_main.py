from models.cart_manager import Cart
from models.pricing_engine import calculate_prices
from models.tax_engine import calculate_tax
from models.stock_manager import deduct_stock
from models.invoice_generator import generate_invoice
from models.transaction_logger import log_transaction

def process_billing(cart_items):

    bill_details, subtotal = calculate_prices(cart_items)
    tax = calculate_tax(bill_details)
    invoice = generate_invoice(bill_details, subtotal, tax)

    deduct_stock(cart_items)
    log_transaction(invoice)

    return invoice


if __name__ == "__main__":
    cart = Cart()
    cart.add_item("morphine", 2)
    cart.add_item("paracetamol", 5)

    invoice = process_billing(cart.get_items())
    print(invoice)