from datetime import datetime
import csv
from io import StringIO
import pandas as pd
from flask import send_file
import pdfkit
import qrcode
import json
import base64
from io import BytesIO

class Storage:
    def __init__(self):
        self.users = {}
        self.products = {}
        self.customers = {}
        self.sales = []
        self.purchases = []
        self.next_product_id = 1
        self.next_customer_id = 1
        self.next_bill_no = 1000

    def add_user(self, username, password_hash):
        self.users[username] = {
            'username': username,
            'password_hash': password_hash
        }

    def get_user(self, username):
        return self.users.get(username)

    def add_product(self, name, price, quantity, barcode=None, unit=None, category=None, 
                   hsn_code=None, gst_rate=0, cess_rate=0):
        product_id = self.next_product_id
        self.products[product_id] = {
            'id': product_id,
            'name': name,
            'price': price,
            'quantity': quantity,
            'barcode': barcode,
            'unit': unit,
            'category': category,
            'hsn_code': hsn_code,
            'gst_rate': gst_rate,
            'cess_rate': cess_rate
        }
        self.next_product_id += 1

    def update_product(self, id, name, price, quantity, barcode=None, unit=None, 
                      category=None, hsn_code=None, gst_rate=0, cess_rate=0):
        if id in self.products:
            self.products[id].update({
                'name': name,
                'price': price,
                'quantity': quantity,
                'barcode': barcode,
                'unit': unit,
                'category': category,
                'hsn_code': hsn_code,
                'gst_rate': gst_rate,
                'cess_rate': cess_rate
            })

    def get_products(self):
        return list(self.products.values())

    def calculate_tax(self, price, quantity, gst_rate, cess_rate=0):
        subtotal = price * quantity
        gst_amount = subtotal * (gst_rate / 100)
        cgst = gst_amount / 2
        sgst = gst_amount / 2
        igst = gst_amount  # For interstate sales
        cess = subtotal * (cess_rate / 100)

        return {
            'subtotal': subtotal,
            'cgst': cgst,
            'sgst': sgst,
            'igst': igst,
            'cess': cess,
            'total': subtotal + gst_amount + cess
        }

    def add_customer(self, name, mobile, email=None, gst_no=None):
        customer_id = self.next_customer_id
        self.customers[customer_id] = {
            'id': customer_id,
            'name': name,
            'mobile': mobile,
            'email': email,
            'gst_no': gst_no,
            'created_at': datetime.now(),
            'total_purchases': 0,
            'last_purchase_date': None
        }
        self.next_customer_id += 1
        return customer_id

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def get_customer_by_mobile(self, mobile):
        return next((customer for customer in self.customers.values() 
                    if customer['mobile'] == mobile), None)

    def get_customer_by_gst(self, gst_no):
        return next((customer for customer in self.customers.values() 
                    if customer['gst_no'] == gst_no), None)

    def get_customers(self):
        return list(self.customers.values())

    def update_customer_stats(self, customer_id, bill_total):
        if customer_id in self.customers:
            self.customers[customer_id]['total_purchases'] += bill_total
            self.customers[customer_id]['last_purchase_date'] = datetime.now()

    def generate_bill_qr(self, bill_data):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(bill_data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered)
        return base64.b64encode(buffered.getvalue()).decode()

    def generate_bill_html(self, sale_items, customer=None, company_info=None):
        bill_no = f"INV-{self.next_bill_no:05d}"
        self.next_bill_no += 1

        bill_data = {
            'bill_no': bill_no,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': sum(item['total'] for item in sale_items)
        }
        qr_code = self.generate_bill_qr(bill_data)

        company_info = company_info or {
            'name': 'Your Company Name',
            'address': 'Your Company Address',
            'gst': 'Your GST Number',
            'phone': 'Your Phone',
            'email': 'your@email.com'
        }
           
        items_html = '\n'.join(
            f"""
            <tr>
                <td>{item['product_name']}</td>
                <td>{item.get('hsn_code', '-')}</td>
                <td>{item['quantity']}</td>
                <td>₹{item['price']:.2f}</td>
                <td>₹{item['subtotal']:.2f}</td>
                <td>{item['gst_rate']}%</td>
                <td>₹{item['gst_amount']:.2f}</td>
                <td>₹{item['total']:.2f}</td>
            </tr>
            """ for item in sale_items
        )

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
                <h1>{company_info['name']}</h1>
                <p>{company_info['address']}</p>
                <p>GST No: {company_info['gst']}</p>
                <h2>Tax Invoice</h2>
            </div>

            <div class="company-details">
                <p>Phone: {company_info['phone']}</p>
                <p>Email: {company_info['email']}</p>
                <p>Invoice No: {bill_no}</p>
                <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="customer-details">
                <h3>Bill To:</h3>
                <p>{customer['name'] if customer else 'Walk-in Customer'}</p>
                {f'<p>Mobile: {customer["mobile"]}</p>' if customer else ''}
                {f'<p>GST No: {customer["gst_no"]}</p>' if customer and customer.get('gst_no') else ''}
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
                    {items_html}
            </table>

            <div class="totals">
                <p><strong>Subtotal:</strong> ₹{sum(item['subtotal'] for item in sale_items):.2f}</p>
                <p><strong>CGST:</strong> ₹{sum(item['gst_amount']/2 for item in sale_items):.2f}</p>
                <p><strong>SGST:</strong> ₹{sum(item['gst_amount']/2 for item in sale_items):.2f}</p>
                <p><strong>Total:</strong> ₹{sum(item['total'] for item in sale_items):.2f}</p>
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

    def generate_bill_pdf(self, sale_items, customer=None, company_info=None):
        html = self.generate_bill_html(sale_items, customer, company_info)

        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
        }

        return pdfkit.from_string(html, False, options=options)

    def add_sale(self, product_id, quantity, price, customer_id=None):
        if product_id in self.products:
            product = self.products[product_id]
            tax_details = self.calculate_tax(
                price, 
                quantity, 
                product['gst_rate'], 
                product['cess_rate']
            )

            sale_data = {
                'date': datetime.now(),
                'product_id': product_id,
                'product_name': product['name'],
                'quantity': quantity,
                'price': price,
                'subtotal': tax_details['subtotal'],
                'cgst': tax_details['cgst'],
                'sgst': tax_details['sgst'],
                'igst': tax_details['igst'],
                'cess': tax_details['cess'],
                'total': tax_details['total'],
                'hsn_code': product['hsn_code'],
                'gst_rate': product['gst_rate'],
                'gst_amount': tax_details['total'] - tax_details['subtotal'] - tax_details['cess'],
                'customer_id': customer_id
            }

            self.sales.append(sale_data)
            self.products[product_id]['quantity'] -= quantity

            if customer_id:
                self.update_customer_stats(customer_id, tax_details['total'])

            return sale_data


    def add_purchase(self, product_id, quantity, price):
        if product_id in self.products:
            product = self.products[product_id]
            tax_details = self.calculate_tax(
                price, 
                quantity, 
                product['gst_rate'], 
                product['cess_rate']
            )

            self.purchases.append({
                'date': datetime.now(),
                'product_id': product_id,
                'product_name': product['name'],
                'quantity': quantity,
                'price': price,
                'subtotal': tax_details['subtotal'],
                'cgst': tax_details['cgst'],
                'sgst': tax_details['sgst'],
                'igst': tax_details['igst'],
                'cess': tax_details['cess'],
                'total': tax_details['total'],
                'hsn_code': product['hsn_code'],
                'gst_rate': product['gst_rate']
            })
            self.products[product_id]['quantity'] += quantity

    def get_sales(self):
        return self.sales

    def get_purchases(self):
        return self.purchases

    def import_products_from_excel(self, file_content):
        df = pd.read_excel(file_content)
        required_columns = ['barcode', 'item_name', 'unit', 'category', 
                          'hsn_code', 'gst_rate', 'price', 'quantity']

        if not all(col in df.columns for col in required_columns):
            raise ValueError("Excel file must contain all required columns")

        for _, row in df.iterrows():
            self.add_product(
                name=row['item_name'],
                price=float(row['price']),
                quantity=int(row['quantity']),
                barcode=str(row['barcode']),
                unit=row['unit'],
                category=row['category'],
                hsn_code=str(row['hsn_code']),
                gst_rate=float(row['gst_rate']),
                cess_rate=float(row.get('cess_rate', 0))
            )

    def export_products_to_excel(self):
        if not self.products:
            return None

        df = pd.DataFrame(self.products.values())
        output = StringIO()
        df.to_excel(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='products_export.xlsx'
        )

    def get_dashboard_stats(self):
        total_sales = sum(sale['total'] for sale in self.sales)
        total_purchases = sum(purchase['total'] for purchase in self.purchases)
        total_inventory = sum(product['quantity'] * product['price'] 
                            for product in self.products.values())
        recent_sales = sorted(self.sales, key=lambda x: x['date'], reverse=True)[:5]
        recent_purchases = sorted(self.purchases, key=lambda x: x['date'], reverse=True)[:5]

        return {
            'total_sales': total_sales,
            'total_purchases': total_purchases,
            'total_inventory': total_inventory,
            'profit': total_sales - total_purchases,
            'recent_sales': recent_sales,
            'recent_purchases': recent_purchases
        }

    def generate_csv_report(self, report_type):
        si = StringIO()
        writer = csv.writer(si)

        if report_type == 'sales':
            writer.writerow(['Date', 'Product', 'HSN', 'Quantity', 'Price', 'Subtotal', 'CGST', 'SGST', 'IGST', 'Total'])
            for sale in self.sales:
                writer.writerow([
                    sale['date'].strftime('%Y-%m-%d %H:%M:%S'),
                    sale['product_name'],
                    sale['hsn_code'],
                    sale['quantity'],
                    sale['price'],
                    sale['subtotal'],
                    sale['cgst'],
                    sale['sgst'],
                    sale['igst'],
                    sale['total']
                ])
        elif report_type == 'purchases':
            writer.writerow(['Date', 'Product', 'HSN', 'Quantity', 'Price', 'Subtotal', 'CGST', 'SGST', 'IGST', 'Total'])
            for purchase in self.purchases:
                writer.writerow([
                    purchase['date'].strftime('%Y-%m-%d %H:%M:%S'),
                    purchase['product_name'],
                    purchase['hsn_code'],
                    purchase['quantity'],
                    purchase['price'],
                    purchase['subtotal'],
                    purchase['cgst'],
                    purchase['sgst'],
                    purchase['igst'],
                    purchase['total']
                ])

        output = si.getvalue()
        si.close()

        return send_file(
            StringIO(output),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{report_type}_report.csv'
        )