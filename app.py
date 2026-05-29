import streamlit as st
import requests

st.set_page_config(page_title="Flipkart Clone", page_icon="🛍️", layout="wide")

# --- CUSTOM FLIPKART STYLE BRANDING ---
st.markdown("""
    <style>
    .main-header { font-size:32px !important; font-weight: bold; color: #2874f0; }
    .product-card { border: 1px solid #f0f0f0; padding: 15px; border-radius: 8px; background-color: white; }
    </style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8001"

# Maintain login credentials globally across pages
if "token" not in st.session_state:
    st.session_state["token"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

# --- TOP NAVIGATION BAR ---
st.markdown('<p class="main-header">Harsha\'s Big Mart</p>', unsafe_allow_html=True)
search_query = st.text_input("🔍 Search for products, brands and more", placeholder="Type item name here...")

# --- LOGIN STATUS SIDEBAR ---
st.sidebar.title("👤 Account")
if st.session_state["token"] is None:
    email = st.sidebar.text_input("Email", value="harsha143@gmail.com")
    password = st.sidebar.text_input("Password", type="password", value="password")
    if st.sidebar.button("Login"):
        res = requests.post(f"{BACKEND_URL}/login", data={"username": email, "password": password})
        if res.status_code == 200:
            st.session_state["token"] = res.json()["access_token"]
            st.session_state["username"] = email
            st.sidebar.success("Logged in successfully!")
            st.rerun()
else:
    st.sidebar.success(f"Welcome back, {st.session_state['username']}!")
    if st.sidebar.button("Log Out"):
        st.session_state["token"] = None
        st.session_state["username"] = None
        st.rerun()

st.sidebar.info("💡 Use the navigation links above to visit your Cart or Seller Dashboard!")

# --- DISPLAY PRODUCT CATALOG ---
st.subheader("Deals of the Day")

try:
    response = requests.get(f"{BACKEND_URL}/products")
    if response.status_code == 200:
        products = response.json()
        
        # Filter products based on search bar input
        if search_query:
            products = [p for p in products if search_query.lower() in p['name'].lower()]

        if not products:
            st.info("No products match your search or the catalog is empty.")
        else:
            cols = st.columns(4)  # 4 item columns like a real retail grid!
            for index, product in enumerate(products):
                with cols[index % 4]:
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    img = product.get("image_url") or "https://images.unsplash.com/photo-1593642632823-8f785ba67e45"
                    st.image(img, use_container_width=True)
                    
                    st.markdown(f"### **{product['name']}**")
                    st.write(f"_{product['description']}_")
                    st.markdown(f"#### 💰 ₹{product['price'] * 80:,.2f}") # Formatted to Rupees!
                    
                    stock = product['stock_quantity']
                    if stock > 0:
                        if st.button(f"🛒 Add to Cart", key=f"shop_{product['id']}", use_container_width=True):
                            if st.session_state["token"] is None:
                                st.warning("Please log in first!")
                            else:
                                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                                cart_res = requests.post(f"{BACKEND_URL}/cart/add", json={"product_id": product['id'], "quantity": 1}, headers=headers)
                                if cart_res.status_code == 201:
                                    st.toast(f"Added {product['name']} to cart!", icon="🛒")
                    else:
                        st.error("Out of Stock")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.write("")
except requests.exceptions.ConnectionError:
    st.error("Backend offline.")