from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, make_response, abort
from storage import Storage
import logging
import pandas as pd
from io import BytesIO
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # In production, use environment variable

# Initialize storage
storage = Storage()

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    stats = storage.get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        if 'action' in request.form:
            if request.form['action'] == 'add':
                storage.add_product(
                    name=request.form['name'],
                    price=float(request.form['price']),
                    quantity=int(request.form['quantity']),
                    barcode=request.form.get('barcode'),
                    unit=request.form.get('unit'),
                    category=request.form.get('category'),
                    hsn_code=request.form.get('hsn_code'),
                    gst_rate=int(request.form.get('gst_rate', 0)),
                    cess_rate=int(request.form.get('cess_rate', 0))
                )
                flash('Product added successfully!', 'success')
            elif request.form['action'] == 'update':
                storage.update_product(
                    id=int(request.form['id']),
                    name=request.form['name'],
                    price=float(request.form['price']),
                    quantity=int(request.form['quantity']),
                    barcode=request.form.get('barcode'),
                    unit=request.form.get('unit'),
                    category=request.form.get('category'),
                    hsn_code=request.form.get('hsn_code'),
                    gst_rate=int(request.form.get('gst_rate', 0)),
                    cess_rate=int(request.form.get('cess_rate', 0))
                )
                flash('Product updated successfully!', 'success')

            elif request.form['action'] == 'import':
                if 'file' not in request.files:
                    flash('No file uploaded', 'error')
                    return redirect(request.url)

                file = request.files['file']
                if file.filename == '':
                    flash('No file selected', 'error')
                    return redirect(request.url)

                if not file.filename.endswith(('.xlsx', '.xls')):
                    flash('Invalid file format. Please upload an Excel file.', 'error')
                    return redirect(request.url)

                try:
                    storage.import_products_from_excel(file)
                    flash('Products imported successfully!', 'success')
                except Exception as e:
                    flash(f'Error importing products: {str(e)}', 'error')

                return redirect(url_for('inventory'))

    products = storage.get_products()
    return render_template('inventory.html', products=products)

@app.route('/inventory/analyze-excel', methods=['POST'])
def analyze_excel():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'status': 'error', 'message': 'Invalid file format'}), 400

    try:
        # Read Excel file
        df = pd.read_excel(file)

        # Get column names
        columns = df.columns.tolist()

        # Get preview data (first 5 rows)
        preview_data = df.head().to_dict('records')

        return jsonify({
            'status': 'success',
            'columns': columns,
            'preview': preview_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error analyzing file: {str(e)}'
        }), 400

@app.route('/inventory/import-excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

    file = request.files['file']
    mappings = request.form.get('mappings')

    if not mappings:
        return jsonify({'status': 'error', 'message': 'No column mappings provided'}), 400

    try:
        mappings = json.loads(mappings)
        df = pd.read_excel(file)

        # Validate required fields
        required_fields = {'name', 'price', 'quantity'}
        mapped_fields = set(mappings.values())
        missing_fields = required_fields - mapped_fields

        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Create reverse mapping (product field -> excel column)
        reverse_mapping = {v: k for k, v in mappings.items() if v}

        # Process each row
        success_count = 0
        errors = []

        for _, row in df.iterrows():
            try:
                product_data = {
                    'name': str(row[reverse_mapping['name']]),
                    'price': float(row[reverse_mapping['price']]),
                    'quantity': int(row[reverse_mapping['quantity']]),
                    'barcode': str(row[reverse_mapping['barcode']]) if 'barcode' in reverse_mapping else None,
                    'unit': str(row[reverse_mapping['unit']]) if 'unit' in reverse_mapping else None,
                    'category': str(row[reverse_mapping['category']]) if 'category' in reverse_mapping else None,
                    'hsn_code': str(row[reverse_mapping['hsn_code']]) if 'hsn_code' in reverse_mapping else None,
                    'gst_rate': float(row[reverse_mapping['gst_rate']]) if 'gst_rate' in reverse_mapping else 0
                }

                storage.add_product(**product_data)
                success_count += 1

            except Exception as e:
                errors.append(f'Error in row {success_count + 1}: {str(e)}')

        return jsonify({
            'status': 'success',
            'message': f'Successfully imported {success_count} products',
            'errors': errors if errors else None
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error importing products: {str(e)}'
        }), 400

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else None

            if data and 'items' in data:
                # Handle multiple items from POS interface
                customer_id = data.get('customer_id')
                sale_items = []

                for item in data['items']:
                    sale_data = storage.add_sale(
                        product_id=int(item['productId']),
                        quantity=int(item['quantity']),
                        price=float(item['price']),
                        customer_id=customer_id
                    )
                    sale_items.append(sale_data)

                # Generate PDF bill
                customer = storage.get_customer(customer_id) if customer_id else None
                pdf_content = storage.generate_bill_pdf(sale_items, customer)

                response = make_response(pdf_content)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = 'inline; filename=bill.pdf'
                return response
            else:
                # Handle single item from form submission
                customer_id = request.form.get('customer_id')
                sale_data = storage.add_sale(
                    product_id=int(request.form['product_id']),
                    quantity=int(request.form['quantity']),
                    price=float(request.form['price']),
                    customer_id=customer_id
                )
                flash('Sale recorded successfully!', 'success')
                return redirect(url_for('sales'))

        except Exception as e:
            logging.error(f"Error recording sale: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 400

    products = storage.get_products()
    sales = storage.get_sales()
    customers = storage.get_customers()
    return render_template('sales.html', 
                         products=products, 
                         sales=sales, 
                         customers=customers)

@app.route('/purchases', methods=['GET', 'POST'])
def purchases():
    if request.method == 'POST':
        storage.add_purchase(
            product_id=int(request.form['product_id']),
            quantity=int(request.form['quantity']),
            price=float(request.form['price'])
        )
        flash('Purchase recorded successfully!', 'success')

    products = storage.get_products()
    purchases = storage.get_purchases()
    return render_template('purchases.html', products=products, purchases=purchases)

@app.route('/reports')
def reports():
    report_type = request.args.get('type', 'sales')
    format_type = request.args.get('format', 'html')

    if format_type == 'csv':
        return storage.generate_csv_report(report_type)

    return render_template('reports.html', 
                         sales=storage.get_sales(),
                         purchases=storage.get_purchases())

@app.route('/sales/<int:sale_id>/pdf')
def get_sale_pdf(sale_id):
    sale = storage.get_sale(sale_id)
    if not sale:
        abort(404)

    customer = None
    if sale.get('customer_id'):
        customer = storage.get_customer(sale.get('customer_id'))

    pdf_content = storage.generate_bill_pdf([sale], customer)

    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=bill.pdf'
    return response

@app.route('/export-products')
def export_products():
    return storage.export_products_to_excel()

if __name__ == '__main__':
    app.run(debug=True)