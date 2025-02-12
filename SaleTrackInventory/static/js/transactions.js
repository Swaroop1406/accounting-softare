// Handle product selection and price auto-fill
document.addEventListener('DOMContentLoaded', function() {
    const productSelect = document.querySelector('select[name="product_id"]');
    const priceInput = document.querySelector('input[name="price"]');
    const quantityInput = document.querySelector('input[name="quantity"]');
    
    if (productSelect && priceInput) {
        // Store product data for quick access
        const products = {};
        Array.from(productSelect.options).forEach(option => {
            if (option.value) {
                const productId = parseInt(option.value);
                const match = option.text.match(/\(Stock: (\d+)\)/);
                const stock = match ? parseInt(match[1]) : 0;
                products[productId] = { stock };
            }
        });

        // Handle product selection
        productSelect.addEventListener('change', function() {
            const productId = parseInt(this.value);
            const product = products[productId];
            
            if (product) {
                // Set max quantity based on available stock (for sales only)
                if (window.location.pathname.includes('/sales')) {
                    quantityInput.max = product.stock;
                    quantityInput.title = `Max available: ${product.stock}`;
                }
            }
        });

        // Validate quantity against stock (for sales only)
        if (window.location.pathname.includes('/sales') && quantityInput) {
            quantityInput.addEventListener('change', function() {
                const productId = parseInt(productSelect.value);
                const product = products[productId];
                
                if (product && this.value > product.stock) {
                    alert(`Only ${product.stock} units available in stock`);
                    this.value = product.stock;
                }
            });
        }
    }

    // Calculate total amount
    const calculateTotal = () => {
        const quantity = parseFloat(quantityInput.value) || 0;
        const price = parseFloat(priceInput.value) || 0;
        const totalElement = document.getElementById('total-amount');
        
        if (totalElement) {
            totalElement.textContent = `$${(quantity * price).toFixed(2)}`;
        }
    };

    if (quantityInput && priceInput) {
        quantityInput.addEventListener('input', calculateTotal);
        priceInput.addEventListener('input', calculateTotal);
    }
});
