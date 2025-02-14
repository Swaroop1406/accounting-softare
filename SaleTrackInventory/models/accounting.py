
from datetime import datetime

class AccountingEntry:
    def __init__(self, date, description, debit=0, credit=0, category=None, reference=None):
        self.date = date
        self.description = description
        self.debit = debit
        self.credit = credit
        self.category = category
        self.reference = reference

class AccountingSystem:
    def __init__(self):
        self.entries = []
        self.categories = ['Sales', 'Purchases', 'Expenses', 'Assets', 'Liabilities']
        
    def add_entry(self, entry):
        self.entries.append(entry)
        
    def get_balance_sheet(self):
        assets = sum(e.debit - e.credit for e in self.entries if e.category == 'Assets')
        liabilities = sum(e.credit - e.debit for e in self.entries if e.category == 'Liabilities')
        equity = assets - liabilities
        return {'assets': assets, 'liabilities': liabilities, 'equity': equity}
        
    def get_income_statement(self, start_date=None, end_date=None):
        sales = sum(e.credit - e.debit for e in self.entries if e.category == 'Sales' 
                   and (not start_date or e.date >= start_date)
                   and (not end_date or e.date <= end_date))
        purchases = sum(e.debit - e.credit for e in self.entries if e.category == 'Purchases'
                       and (not start_date or e.date >= start_date)
                       and (not end_date or e.date <= end_date))
        expenses = sum(e.debit - e.credit for e in self.entries if e.category == 'Expenses'
                      and (not start_date or e.date >= start_date)
                      and (not end_date or e.date <= end_date))
        profit = sales - purchases - expenses
        return {
            'sales': sales,
            'purchases': purchases,
            'expenses': expenses,
            'profit': profit
        }
