-- LegacyShop Seed Data
-- This file populates the database with sample data for testing and demonstration

-- Insert sample products with varied pricing to test discount tiers
INSERT INTO products (sku, name, description, price, stock_quantity, active) VALUES
('LAPTOP-001', 'Business Laptop Pro', 'High-performance laptop for business users with 16GB RAM, 512GB SSD', 1299.99, 25, TRUE),
('LAPTOP-002', 'Gaming Laptop Ultra', 'Gaming laptop with RTX graphics, 32GB RAM, 1TB SSD', 2499.99, 15, TRUE),
('MOUSE-001', 'Wireless Mouse Premium', 'Ergonomic wireless mouse with precision tracking', 79.99, 100, TRUE),
('KEYBOARD-001', 'Mechanical Keyboard RGB', 'RGB backlit mechanical keyboard with blue switches', 149.99, 50, TRUE),
('MONITOR-001', '4K Monitor 27"', '27-inch 4K IPS monitor with USB-C connectivity', 399.99, 30, TRUE),
('HEADSET-001', 'Noise Cancelling Headset', 'Professional noise-cancelling headset for remote work', 249.99, 40, TRUE),
('WEBCAM-001', '4K Webcam Pro', '4K webcam with auto-focus and noise reduction', 199.99, 35, TRUE),
('ADAPTER-001', 'USB-C Hub Multi-Port', '7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader', 89.99, 75, TRUE),
('CABLE-001', 'Thunderbolt 4 Cable', '2m Thunderbolt 4 cable supporting 40Gbps data transfer', 49.99, 200, TRUE),
('STAND-001', 'Laptop Stand Adjustable', 'Adjustable aluminum laptop stand for better ergonomics', 59.99, 60, TRUE),
('CHARGER-001', '100W USB-C Charger', 'Fast-charging 100W USB-C power adapter', 79.99, 80, TRUE),
('BAG-001', 'Laptop Backpack Pro', 'Water-resistant laptop backpack with multiple compartments', 129.99, 45, TRUE),
('DOCK-001', 'Docking Station Pro', 'Universal docking station with dual 4K display support', 299.99, 20, TRUE),
('SPEAKER-001', 'Bluetooth Speaker', 'Portable Bluetooth speaker with 20-hour battery life', 99.99, 65, TRUE),
('TABLET-001', 'Business Tablet 12"', '12-inch business tablet with stylus and keyboard cover', 799.99, 18, TRUE);

-- Insert sample customers with varying loyalty points
INSERT INTO customers (email, first_name, last_name, loyalty_points) VALUES
('john.doe@example.com', 'John', 'Doe', 150),
('jane.smith@example.com', 'Jane', 'Smith', 325),
('mike.johnson@example.com', 'Mike', 'Johnson', 75),
('sarah.wilson@example.com', 'Sarah', 'Wilson', 480), -- Near the 500 cap
('david.brown@example.com', 'David', 'Brown', 0),     -- New customer
('lisa.garcia@example.com', 'Lisa', 'Garcia', 250),
('james.miller@example.com', 'James', 'Miller', 120),
('emma.davis@example.com', 'Emma', 'Davis', 390),
('robert.taylor@example.com', 'Robert', 'Taylor', 45),
('olivia.anderson@example.com', 'Olivia', 'Anderson', 500); -- At the cap

-- Insert sample orders with different statuses and totals to test business rules
INSERT INTO orders (customer_id, status, subtotal, discount_amount, total, idempotency_key) VALUES
(1, 'PAID', 1299.99, 194.99, 1104.99, 'ORDER-001-JOHN'),      -- Laptop order with 15% discount (tier 3)
(2, 'PAID', 329.98, 32.99, 296.99, 'ORDER-002-JANE'),        -- Headset + Mouse with 10% discount (tier 2)
(3, 'PENDING', 149.99, 7.50, 142.49, 'ORDER-003-MIKE'),      -- Keyboard with 5% discount (tier 1)
(4, 'SHIPPED', 599.98, 59.99, 539.99, 'ORDER-004-SARAH'),    -- Monitor + Webcam with 10% discount
(5, 'CANCELLED', 79.99, 4.00, 75.99, 'ORDER-005-DAVID'),     -- Mouse order (cancelled)
(6, 'PAID', 89.99, 4.50, 85.49, 'ORDER-006-LISA'),          -- USB Hub with 5% discount
(7, 'PENDING', 2499.99, 374.99, 2124.99, 'ORDER-007-JAMES'), -- Gaming laptop with 15% discount
(8, 'PAID', 179.98, 8.99, 170.99, 'ORDER-008-EMMA'),        -- Keyboard + Stand with 5% discount
(9, 'PAID', 49.99, 0.00, 49.99, 'ORDER-009-ROBERT'),        -- Cable (no discount - below $50)
(10, 'SHIPPED', 929.98, 139.50, 790.48, 'ORDER-010-OLIVIA'); -- Tablet + Bag with 15% discount

-- Insert corresponding order items
INSERT INTO order_items (order_id, product_id, product_sku, product_name, quantity, unit_price, subtotal) VALUES
-- Order 1: John's laptop
(1, 1, 'LAPTOP-001', 'Business Laptop Pro', 1, 1299.99, 1299.99),

-- Order 2: Jane's headset and mouse
(2, 6, 'HEADSET-001', 'Noise Cancelling Headset', 1, 249.99, 249.99),
(2, 3, 'MOUSE-001', 'Wireless Mouse Premium', 1, 79.99, 79.99),

-- Order 3: Mike's keyboard
(3, 4, 'KEYBOARD-001', 'Mechanical Keyboard RGB', 1, 149.99, 149.99),

-- Order 4: Sarah's monitor and webcam
(4, 5, 'MONITOR-001', '4K Monitor 27"', 1, 399.99, 399.99),
(4, 7, 'WEBCAM-001', '4K Webcam Pro', 1, 199.99, 199.99),

-- Order 5: David's cancelled mouse order
(5, 3, 'MOUSE-001', 'Wireless Mouse Premium', 1, 79.99, 79.99),

-- Order 6: Lisa's USB hub
(6, 8, 'ADAPTER-001', 'USB-C Hub Multi-Port', 1, 89.99, 89.99),

-- Order 7: James's gaming laptop
(7, 2, 'LAPTOP-002', 'Gaming Laptop Ultra', 1, 2499.99, 2499.99),

-- Order 8: Emma's keyboard and stand
(8, 4, 'KEYBOARD-001', 'Mechanical Keyboard RGB', 1, 149.99, 149.99),
(8, 10, 'STAND-001', 'Laptop Stand Adjustable', 1, 59.99, 29.99),

-- Order 9: Robert's cable
(9, 9, 'CABLE-001', 'Thunderbolt 4 Cable', 1, 49.99, 49.99),

-- Order 10: Olivia's tablet and bag
(10, 15, 'TABLET-001', 'Business Tablet 12"', 1, 799.99, 799.99),
(10, 12, 'BAG-001', 'Laptop Backpack Pro', 1, 129.99, 129.99);

-- Insert payment records for PAID orders
INSERT INTO payments (order_id, status, amount, external_authorization_id, retry_attempts) VALUES
(1, 'AUTHORIZED', 1104.99, 'AUTH_12345_JOHN', 0),
(2, 'AUTHORIZED', 296.99, 'AUTH_12346_JANE', 0),
(6, 'AUTHORIZED', 85.49, 'AUTH_12347_LISA', 0),
(8, 'AUTHORIZED', 170.99, 'AUTH_12348_EMMA', 0),
(9, 'AUTHORIZED', 49.99, 'AUTH_12349_ROBERT', 0),
(10, 'AUTHORIZED', 790.48, 'AUTH_12350_OLIVIA', 0);

-- Insert sample audit logs to show business activity
INSERT INTO audit_logs (operation, entity_type, entity_id, details) VALUES
('PRODUCT_CREATED', 'Product', 1, 'Created product with SKU: LAPTOP-001'),
('PRODUCT_CREATED', 'Product', 2, 'Created product with SKU: LAPTOP-002'),
('ORDER_CREATED', 'Order', 1, 'Order created for customer john.doe@example.com'),
('PAYMENT_AUTHORIZED', 'Payment', 1, 'Payment authorized for order 1'),
('ORDER_CREATED', 'Order', 2, 'Order created for customer jane.smith@example.com'),
('LOYALTY_POINTS_ADDED', 'Customer', 1, 'Added 110 loyalty points for order 1'),
('ORDER_CANCELLED', 'Order', 5, 'Order cancelled: Customer requested cancellation'),
('INVENTORY_REPLENISHMENT', 'Product', 3, 'Replenished 50 units of product MOUSE-001'),
('INVENTORY_REPLENISHMENT', 'System', NULL, 'Nightly replenishment completed. 3 products restocked with 100 units each');

-- Insert some idempotency records to show the pattern
INSERT INTO idempotency_records (idempotency_key, operation_type, result_entity_id, result_data) VALUES
('ORDER-001-JOHN', 'ORDER_CREATE', 1, 'PAID'),
('ORDER-002-JANE', 'ORDER_CREATE', 2, 'PAID'),
('LOYALTY_1', 'LOYALTY_POINTS', 1, '110'),
('LOYALTY_2', 'LOYALTY_POINTS', 2, '30');

-- Update product stock to reflect orders (simulate the atomic decrements that would have occurred)
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'LAPTOP-001';      -- Order 1
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'HEADSET-001';    -- Order 2
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'MOUSE-001';      -- Order 2
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'KEYBOARD-001';   -- Order 3
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'MONITOR-001';    -- Order 4
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'WEBCAM-001';     -- Order 4
-- Note: Order 5 was cancelled, so stock for MOUSE-001 was restored
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'ADAPTER-001';    -- Order 6
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'LAPTOP-002';     -- Order 7
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'KEYBOARD-001';   -- Order 8 (second keyboard)
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'STAND-001';      -- Order 8
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'CABLE-001';      -- Order 9
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'TABLET-001';     -- Order 10
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE sku = 'BAG-001';        -- Order 10;