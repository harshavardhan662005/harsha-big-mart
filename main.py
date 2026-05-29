import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, SessionLocal

# Create database tables automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Commerce API")

# Security and JWT Constants
SECRET_KEY = "SUPER_SECRET_KEY_FOR_LOCAL_DEV_DONT_SHARE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- NATIVE PASSWORD HASHING FUNCTION ---
def get_password_hash(password: str) -> str:
    """Hash a password securely using native SHA-256 with a random salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify an incoming plain password against the stored salt$hash"""
    try:
        salt, stored_hash = hashed_password.split("$")
        hash_obj = hashlib.sha256((plain_password + salt).encode())
        return hash_obj.hexdigest() == stored_hash
    except ValueError:
        return False

# --- DATABASE DEPENDENCY ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTHENTICATION DEPENDENCIES ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Extract and validate JWT token to get the current user"""
    import jwt
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email, role=payload.get("role"))
    except Exception:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def verify_admin(current_user: models.User = Depends(get_current_user)):
    """Ensure the authenticated user is an Admin"""
    # Force access if it's your admin email or if the role matches
    if current_user.email == "harsha143@gmail.com" or current_user.role in ["Admin", "admin", "ADMIN"]:
        return current_user
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The requested operation requires Admin privileges"
    )
# --- USER ENDPOINTS ---

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user or admin"""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    
    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_pwd,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return a JWT Access Token"""
    import jwt
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + access_token_expires
    to_encode = {"sub": db_user.email, "role": db_user.role, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}

# --- PRODUCT CRUD ENDPOINTS ---

@app.post("/products", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """ADMIN ONLY: Add a new product to the catalog"""
    new_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        image_url=product.image_url  # <-- ADD THIS LINE
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product
@app.get("/products", response_model=list[schemas.ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    """PUBLIC: View the entire product catalog"""
    return db.query(models.Product).all()

@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def get_single_product(product_id: int, db: Session = Depends(get_db)):
    """PUBLIC: Get details of a specific product by its ID"""
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), admin_user: models.User = Depends(verify_admin)):
    """ADMIN ONLY: Delete a product from the database"""
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return None
# --- SHOPPING CART & CHECKOUT ENDPOINTS ---

# --- SHOPPING CART & CHECKOUT ENDPOINTS ---

@app.post("/cart/add", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(item: schemas.CartItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """USER ONLY: Add a product to an active Pending order (acting as a shopping cart)"""
    # 1. Verify product exists and check stock
    product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock_quantity < item.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Only {product.stock_quantity} remaining.")

    # 2. Find or create an active 'Pending' order for this user
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.status == "Pending").first()
    if not order:
        order = models.Order(user_id=current_user.id, total_amount=0.0, status="Pending")
        db.add(order)
        db.commit()
        db.refresh(order)

    # 3. Check if product is already in the cart
    cart_item = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id, models.OrderItem.product_id == item.product_id).first()
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=product.price
        )
        db.add(cart_item)

    # 4. Recalculate total amount
    db.commit()
    db.refresh(order)
    
    all_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).all()
    order.total_amount = sum(float(i.price_at_purchase) * i.quantity for i in all_items)
    db.commit()
    db.refresh(order)
    
    return order

@app.get("/cart", response_model=schemas.OrderResponse)
def view_cart(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """USER ONLY: View items currently resting inside your cart"""
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.status == "Pending").first()
    if not order:
        raise HTTPException(status_code=404, detail="Your shopping cart is completely empty")
    return order

@app.post("/cart/checkout", response_model=schemas.OrderResponse)
def checkout(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """USER ONLY: Convert pending cart into a formal processed order and deduct inventory stock"""
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.status == "Pending").first()
    if not order or not order.items:
        raise HTTPException(status_code=400, detail="Cannot checkout an empty shopping cart")

    # Double check stock capacities before confirming changes
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stock for '{product.name}' dropped since adding to cart. Checkout halted.")
        
        # Deduct the stock inventory count
        product.stock_quantity -= item.quantity

    # Advance order stage status
    order.status = "Processing"
    db.commit()
    db.refresh(order)
    return order