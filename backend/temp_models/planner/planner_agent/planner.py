from planner_agent.workflow_manager import WorkflowManager

class Planner:
    def __init__(self, stock_checker, prescription_analyzer, billing_processor):
        self.workflow_manager = WorkflowManager(stock_checker, prescription_analyzer, billing_processor)

    def execute_workflow(self, order_items, prescription_image_path):
        # Step 1: Check stock
        stock_result = self.workflow_manager.check_stock(order_items)
        if stock_result["status"] != "success":
            return self._build_response("FAILED", stock_result["message"])

        # Step 2: Validate prescription
        prescription_result = self.workflow_manager.validate_prescription(prescription_image_path)
        if prescription_result["status"] != "success":
            return self._build_response("FAILED", prescription_result["message"], validation_result=prescription_result["validation_result"])

        # Step 3: Generate bill
        bill_result = self.workflow_manager.generate_bill(order_items)
        if bill_result["status"] != "success":
            return self._build_response("FAILED", bill_result["message"])

        # Step 4: Await confirmation
        return self._build_response("AWAITING_CONFIRMATION", "Awaiting confirmation.", validation_result=prescription_result["validation_result"], invoice=bill_result["invoice"])

    def confirm_order(self, invoice_id, confirm):
        confirmation_result = self.workflow_manager.confirm_order(invoice_id, confirm)
        return self._build_response(self.workflow_manager.state_machine.get_state(), confirmation_result["message"])

    def _build_response(self, state, message, validation_result=None, invoice=None):
        return {
            "state": state,
            "message": message,
            "validation_result": validation_result,
            "invoice": invoice,
        }