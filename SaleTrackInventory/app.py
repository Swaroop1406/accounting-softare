from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, make_response, abort
from flask_login import LoginManager, login_required, current_user
from storage import Storage
from auth import init_auth, User
import logging
import pandas as pd
from io import BytesIO
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # In production, use environment variable

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize storage
storage = Storage()

# Initialize authentication
init_auth(app, login_manager, storage)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    stats = storage.get_dashboard_stats()
    return render_template('dashboard.html', stats=stats, user=current_user)

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        if 'action' in request.form:
            if request.form['action'] == 'add':
                storage.add_product(
                    name=request.form['name'],
                    price=float(request.form['price']),
                    quantity=int(request.form['quantity']),
                    mrp=float(request.form['mrp']),
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
                    mrp=float(request.form['mrp']),
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
        # Save file content
        file_content = file.read()

        # Create BytesIO object and write content
        excel_file = BytesIO(file_content)

        # Read Excel file using pandas with explicit engine
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(excel_file, engine='openpyxl')
        else:
            df = pd.read_excel(excel_file, engine='xlrd')

        # Reset file pointer
        excel_file.seek(0)

        if df.empty:
            return jsonify({'status': 'error', 'message': 'Excel file is empty'}), 400

        # Get column names
        columns = df.columns.tolist()

        # Get preview data (first 5 rows)
        preview_data = df.head().to_dict('records')

        # Convert all data to string format for JSON serialization
        preview_data = [{k: str(v) for k, v in row.items()} for row in preview_data]

        return jsonify({
            'status': 'success',
            'columns': columns,
            'preview': preview_data
        })
    except Exception as e:
        logging.error(f"Excel analysis error: {str(e)}")
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

        # Create reverse mapping
        reverse_mapping = {v: k for k, v in mappings.items() if v}

        # Validate required fields
        required_fields = {'name', 'price', 'quantity'}
        mapped_fields = set(mappings.values())
        missing_fields = required_fields - mapped_fields

        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Process each row
        success_count = 0
        errors = []
        valid_products = []

        for idx, row in df.iterrows():
            try:
                # Basic validation
                name = str(row[reverse_mapping['name']]).strip()
                if not name:
                    raise ValueError("Product name cannot be empty")

                price = float(row[reverse_mapping['price']])
                if price <= 0:
                    raise ValueError("Price must be greater than 0")

                quantity = int(row[reverse_mapping['quantity']])
                if quantity < 0:
                    raise ValueError("Quantity cannot be negative")

                # GST validation
                gst_rate = 0
                if 'gst_rate' in reverse_mapping:
                    gst_rate = float(row[reverse_mapping['gst_rate']])
                    if gst_rate not in [0, 5, 12, 18, 28]:
                        raise ValueError("Invalid GST rate. Must be 0, 5, 12, 18, or 28")

                # Construct product data
                product_data = {
                    'name': name,
                    'price': price,
                    'quantity': quantity,
                    'barcode': str(row[reverse_mapping['barcode']]).strip() if 'barcode' in reverse_mapping else None,
                    'unit': str(row[reverse_mapping['unit']]).strip() if 'unit' in reverse_mapping else None,
                    'category': str(row[reverse_mapping['category']]).strip() if 'category' in reverse_mapping else None,
                    'hsn_code': str(row[reverse_mapping['hsn_code']]).strip() if 'hsn_code' in reverse_mapping else None,
                    'gst_rate': gst_rate
                }

                # Check for duplicate barcodes if provided
                if product_data['barcode'] and storage.get_product_by_barcode(product_data['barcode']):
                    raise ValueError(f"Duplicate barcode: {product_data['barcode']}")

                valid_products.append(product_data)
                success_count += 1

            except Exception as e:
                errors.append(f'Error in row {idx + 1}: {str(e)}')

        # Only add products if there are no errors
        if not errors:
            for product_data in valid_products:
                storage.add_product(**product_data)

            return jsonify({
                'status': 'success',
                'message': f'Successfully imported {success_count} products'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Validation errors found',
                'errors': errors
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error importing products: {str(e)}'
        }), 400

@app.route('/sales', methods=['GET', 'POST'])
@login_required
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
@login_required
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
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if report_type == 'balance_sheet':
        data = storage.accounting.get_balance_sheet()
        return render_template('reports.html', balance_sheet=data)
    elif report_type == 'income_statement':
        data = storage.accounting.get_income_statement(start_date, end_date)
        return render_template('reports.html', income_statement=data)
    elif format_type == 'excel':
        return storage.export_report_to_excel(report_type, start_date, end_date)

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