class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, name, quantity):
        self.items.append({
            "name": name.lower(),
            "quantity": quantity
        })

    def get_items(self):
        return self.items