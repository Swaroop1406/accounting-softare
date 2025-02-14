import pdfkit
import qrcode
from io import BytesIO
import base64
import json
from datetime import datetime

class BillGenerator:
    def __init__(self, company_name, company_address, company_gst, company_phone, company_email):
        self.company_name = company_name
        self.company_address = company_address
        self.company_gst = company_gst
        self.company_phone = company_phone
        self.company_email = company_email

    def generate_qr_code(self, bill):
        """Generate QR code with bill details"""
        qr_data = {
            'bill_no': bill.bill_no,
            'date': bill.date.strftime('%Y-%m-%d %H:%M:%S'),
            'amount': float(bill.total),
            'company_gst': self.company_gst
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered)
        return base64.b64encode(buffered.getvalue()).decode()

    def generate_html(self, bill):
        """Generate HTML template for the bill"""
        qr_code = self.generate_qr_code(bill)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Tax Invoice</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .company-details {{ margin-bottom: 20px; }}
                .customer-details {{ margin-bottom: 20px; }}
                .bill-items {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .bill-items th, .bill-items td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .totals {{ float: right; width: 300px; }}
                .qr-code {{ text-align: center; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{self.company_name}</h1>
                <p>{self.company_address}</p>
                <p>GST No: {self.company_gst}</p>
                <h2>Tax Invoice</h2>
            </div>

            <div class="company-details">
                <p>Phone: {self.company_phone}</p>
                <p>Email: {self.company_email}</p>
                <p>Invoice No: {bill.bill_no}</p>
                <p>Date: {bill.date.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="customer-details">
                <h3>Bill To:</h3>
                <p>{bill.customer.name if bill.customer else 'Walk-in Customer'}</p>
                {f'<p>Mobile: {bill.customer.mobile}</p>' if bill.customer else ''}
                {f'<p>GST No: {bill.customer.gst_no}</p>' if bill.customer and bill.customer.gst_no else ''}
            </div>

            <table class="bill-items">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>HSN</th>
                        <th>Quantity</th>
                        <th>Rate</th>
                        <th>Amount</th>
                        <th>GST %</th>
                        <th>GST Amt</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f"""
                    <tr>
                        <td>{item['product_name']}</td>
                        <td>{item.get('hsn_code', '-')}</td>
                        <td>{item['quantity']}</td>
                        <td>₹{item['price']:.2f}</td>
                        <td>₹{item['subtotal']:.2f}</td>
                        <td>{item['gst_rate']}%</td>
                        <td>₹{item['gst_amount']:.2f}</td>
                        <td>₹{(item['subtotal'] + item['gst_amount']):.2f}</td>
                    </tr>
                    """ for item in bill.items)}
                </tbody>
            </table>

            <div class="totals">
                <p><strong>Subtotal:</strong> ₹{bill.subtotal:.2f}</p>
                <p><strong>CGST:</strong> ₹{bill.total_gst/2:.2f}</p>
                <p><strong>SGST:</strong> ₹{bill.total_gst/2:.2f}</p>
                <p><strong>Total:</strong> ₹{bill.total:.2f}</p>
            </div>

            <div class="qr-code">
                <img src="data:image/png;base64,{qr_code}" width="150">
                <p>Scan to verify bill</p>
            </div>

            <div class="footer">
                <p>This is a computer generated invoice</p>
            </div>
        </body>
        </html>
        """
        return html

    def generate_pdf(self, bill, output_path=None):
        """Generate PDF bill"""
        html = self.generate_html(bill)
        
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
        }
        
        if output_path:
            pdfkit.from_string(html, output_path, options=options)
        else:
            return pdfkit.from_string(html, False, options=options)
