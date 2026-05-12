from .bank_funcs import Bank
from .inventory_funcs import Inventory

class Database:
    def __init__(self, filename):
        self.filename = filename
        self.bank = Bank(self)
        self.inv = Inventory(self)
