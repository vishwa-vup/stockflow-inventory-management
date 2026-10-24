import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.product import Product
from app.auth.security import hash_password

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create test admin
    admin = User(
        name="Admin Test",
        email="admintest@stockflow.com",
        password_hash=hash_password("Admin@123"),
        role="ADMIN",
        is_active=True
    )
    # Create test staff
    staff = User(
        name="Staff Test",
        email="stafftest@stockflow.com",
        password_hash=hash_password("Staff@123"),
        role="STAFF",
        is_active=True
    )
    # Create test category
    cat = Category(name="Electronics", description="Electronic devices")
    # Create test supplier
    sup = Supplier(name="Apex Supplies", contact_person="John", phone="12345", email="apex@test.com")
    db.add_all([admin, staff, cat, sup])
    db.commit()

    # Create a product
    prod = Product(
        product_code="TEST-PRD-01",
        name="Test Laptop",
        description="Testing device",
        category_id=cat.id,
        supplier_id=sup.id,
        purchase_price=500.0,
        selling_price=800.0,
        current_stock=10,
        minimum_stock=5,
        maximum_stock=50,
        location="Shelf 1"
    )
    db.add(prod)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
