import streamlit as st
import requests

st.set_page_config(page_title="Seller Central", layout="wide")
st.title("⚙️ Flipkart Seller Central Dashboard")

BACKEND_URL = "http://127.0.0.1:8001"

if st.session_state.get("token") is None:
    st.warning("⚠️ Access Denied. Please log in as an administrator on the Home page.")
else:
    st.subheader("Add a New Product to Flipkart Catalog")
    with st.form("seller_form"):
        name = st.text_input("Product Name")
        desc = st.text_area("Product Description")
        price = st.number_input("Price (USD base value)", min_value=1.0, value=10.0)
        stock = st.number_input("Stock Volume Available", min_value=1, value=100)
        img_url = st.text_input("Image Web Link URL")
        
        submit = st.form_submit_button("Launch Product Live")
        
        if submit:
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            payload = {"name": name, "description": desc, "price": price, "stock_quantity": int(stock), "image_url": img_url}
            res = requests.post(f"{BACKEND_URL}/products", json=payload, headers=headers)
            if res.status_code == 201:
                st.success(f"🚀 {name} is now live on Flipkart storefront!")
            else:
                st.error("Failed to upload. Please verify admin role permissions.")