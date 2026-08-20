CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    event_type ENUM('view', 'add_to_cart', 'purchase') NOT NULL,
    product_id VARCHAR(64) NOT NULL,
    value DECIMAL(10,2) NULL,
    event_timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);