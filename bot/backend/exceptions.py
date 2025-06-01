class DuplicateLabelError(Exception):
    def __init__(self, label: str):
        super().__init__(f"SIP config with label '{label}' already exists.")
        self.label = label

class InsufficientAmountError(Exception):
    def __init__(self, message: str = "Insufficient amount"):
        super().__init__(message)