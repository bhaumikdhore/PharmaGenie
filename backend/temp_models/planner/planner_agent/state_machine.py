class StateMachine:
    def __init__(self):
        self.state = "INIT"

    def transition(self, new_state):
        valid_states = [
            "INIT",
            "STOCK_CHECKED",
            "PRESCRIPTION_VALIDATED",
            "BILL_GENERATED",
            "AWAITING_CONFIRMATION",
            "COMPLETED",
            "FAILED",
        ]
        if new_state in valid_states:
            self.state = new_state
        else:
            raise ValueError(f"Invalid state transition: {new_state}")

    def get_state(self):
        return self.state