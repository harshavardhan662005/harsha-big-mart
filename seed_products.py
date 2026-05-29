import requests

BACKEND_URL = "http://127.0.0.1:8001"

# 1. Log in to get the admin token automatically
login_payload = {"username": "harsha143@gmail.com", "password": "password"}
try:
    res = requests.post(f"{BACKEND_URL}/login", data=login_payload)
    if res.status_code != 200:
        print("❌ Error: Could not authenticate. Make sure your backend is running and your user exists.")
        exit()
    
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Define a rich catalog of items to add
    bulk_products = [
        {
            "name": "Sony WH-1000XM4 Headphones",
            "description": "Premium noise-canceling over-ear headphones with long battery life.",
            "price": 249.99,
            "stock_quantity": 15,
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"
        },
        {
            "name": "iPhone 15 Pro Silicone Case",
            "description": "MagSafe compatible sleek midnight black protective case.",
            "price": 49.99,
            "stock_quantity": 40,
            "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"
        },
        {
            "name": "Minimalist Leather Wallet",
            "description": "Slim RFID-blocking genuine leather bi-fold wallet.",
            "price": 29.99,
            "stock_quantity": 25,
            "image_url": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=500"
        },
        {
            "name": "Mechanical Gaming Keyboard",
            "description": "RGB backlit tactile mechanical switches with custom keycaps.",
            "price": 89.99,
            "stock_quantity": 12,
            "image_url": "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=500"
        },
        {
            "name": "Ergonomic Wireless Mouse",
            "description": "High-precision optical tracking mouse with vertical comfort grip.",
            "price": 59.99,
            "stock_quantity": 20,
            "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500"
        },
        {
            "name": "Stainless Steel Water Bottle",
            "description": "Double-wall vacuum insulated flask, keeps drinks cold for 24 hours.",
            "price": 24.99,
            "stock_quantity": 50,
            "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500"
        }
    ]

    # 3. Loop through and push them into the database
    print("🚀 Injecting items into your e-commerce engine...")
    for product in bulk_products:
        response = requests.post(f"{BACKEND_URL}/products", json=product, headers=headers)
        if response.status_code == 201:
            print(f"✅ Successfully added: {product['name']}")
        else:
            print(f"❌ Failed to add {product['name']}: {response.text}")

    print("\n🎉 Done! All items have been loaded successfully.")

except requests.exceptions.ConnectionError:
    print("🚨 Error: Backend server is offline! Please make sure uvicorn is running on port 8001.")