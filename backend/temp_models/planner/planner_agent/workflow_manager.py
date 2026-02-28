from planner_agent.state_machine import StateMachine

class WorkflowManager:
    def __init__(self, stock_checker, prescription_analyzer, billing_processor):
        self.state_machine = StateMachine()
        self.stock_checker = stock_checker
        self.prescription_analyzer = prescription_analyzer
        self.billing_processor = billing_processor

    def check_stock(self, order_items):
        # Simulate stock check
        stock_available = all(item.get("in_stock", False) for item in order_items)
        if stock_available:
            self.state_machine.transition("STOCK_CHECKED")
            return {"status": "success", "message": "Stock available."}
        else:
            self.state_machine.transition("FAILED")
            return {"status": "error", "message": "Stock unavailable."}

    def validate_prescription(self, prescription_image_path):
        result = self.prescription_analyzer(prescription_image_path)
        if result["status"] == "success" and result["decision"] == "APPROVED":
            self.state_machine.transition("PRESCRIPTION_VALIDATED")
            return {"status": "success", "message": "Prescription validated.", "validation_result": result}
        else:
            self.state_machine.transition("FAILED")
            return {"status": "error", "message": "Prescription validation failed.", "validation_result": result}

    def generate_bill(self, cart_items):
        invoice = self.billing_processor(cart_items)
        self.state_machine.transition("BILL_GENERATED")
        return {"status": "success", "message": "Bill generated.", "invoice": invoice}

    def confirm_order(self, invoice_id, confirm):
        if confirm:
            self.state_machine.transition("COMPLETED")
            return {"status": "success", "message": "Order completed."}
        else:
            self.state_machine.transition("FAILED")
            return {"status": "error", "message": "Order cancelled."}