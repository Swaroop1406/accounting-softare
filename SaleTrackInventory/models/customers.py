from datetime import datetime

class Customer:
    def __init__(self, name, mobile, email=None, gst_no=None):
        self.id = None  # Will be set when added to storage
        self.name = name
        self.mobile = mobile
        self.email = email
        self.gst_no = gst_no
        self.created_at = datetime.now()
        self.total_purchases = 0
        self.last_purchase_date = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mobile': self.mobile,
            'email': self.email,
            'gst_no': self.gst_no,
            'created_at': self.created_at,
            'total_purchases': self.total_purchases,
            'last_purchase_date': self.last_purchase_date
        }

class Bill:
    def __init__(self, customer, items, bill_no):
        self.bill_no = bill_no
        self.customer = customer
        self.items = items
        self.date = datetime.now()
        self.subtotal = sum(item['subtotal'] for item in items)
        self.total_gst = sum(item['gst_amount'] for item in items)
        self.total = self.subtotal + self.total_gst
        self.payment_method = None
        self.status = 'pending'

    def to_dict(self):
        return {
            'bill_no': self.bill_no,
            'customer': self.customer.to_dict() if self.customer else None,
            'items': self.items,
            'date': self.date,
            'subtotal': self.subtotal,
            'total_gst': self.total_gst,
            'total': self.total,
            'payment_method': self.payment_method,
            'status': self.status
        }
