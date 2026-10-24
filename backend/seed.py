import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure parent directory is in path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.transaction import Transaction
from app.auth.security import hash_password

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_admin = db.query(User).filter(User.email == "admin@stockflow.com").first()
        if existing_admin:
            print("Database already contains seed data. Skipping seed process.")
            return

        print("Seeding Users...")
        admin = User(
            name="Alexander Wright",
            email="admin@stockflow.com",
            password_hash=hash_password("Admin@123"),
            role="ADMIN",
            is_active=True
        )
        staff1 = User(
            name="John Miller",
            email="john@stockflow.com",
            password_hash=hash_password("Staff@123"),
            role="STAFF",
            is_active=True
        )
        staff2 = User(
            name="Sarah Jenkins",
            email="sarah@stockflow.com",
            password_hash=hash_password("Staff@123"),
            role="STAFF",
            is_active=True
        )
        db.add_all([admin, staff1, staff2])
        db.commit()
        db.refresh(admin)
        db.refresh(staff1)
        db.refresh(staff2)
        print(f"-> Created 3 users: 1 Admin ({admin.email}), 2 Staff ({staff1.email}, {staff2.email})")

        print("Seeding Categories...")
        categories_data = [
            ("Electronics & Computing", "Desktop computers, laptops, tablets, and core computing hardware"),
            ("Computer Peripherals", "Keyboards, mice, webcams, monitors, and input/output accessories"),
            ("Office Furniture", "Ergonomic chairs, standing desks, lamps, and workspace fixtures"),
            ("Office Supplies & Stationery", "Notebooks, executive pens, binders, and daily consumable office stationery"),
            ("Cables & Adapters", "High-speed USB cables, HDMI cords, power adapters, and networking patches")
        ]
        category_map = {}
        for name, desc in categories_data:
            cat = Category(name=name, description=desc)
            db.add(cat)
            db.commit()
            db.refresh(cat)
            category_map[name] = cat
        print(f"-> Created {len(category_map)} categories.")

        print("Seeding Suppliers...")
        suppliers_data = [
            ("TechDistro Global Ltd", "Marcus Vance", "+1-555-0192", "marcus@techdistro.com", "100 Innovation Blvd", "San Jose", "California", "GSTIN06AAAAA0000A1Z5"),
            ("Apex Peripherals Corp", "Elena Rostova", "+1-555-0144", "elena@apexperiph.com", "45 Harbor View Way", "Seattle", "Washington", "GSTIN27BBBBB1111B2Z6"),
            ("Ergonomics World Inc", "David Kim", "+1-555-0178", "david@ergoworld.com", "782 Commerce Dr", "Austin", "Texas", "GSTIN29CCCCC2222C3Z7"),
            ("Prime Office Supplies", "Rachel Green", "+1-555-0129", "rachel@primeofficesupplies.com", "550 Paper Mill Rd", "Chicago", "Illinois", "GSTIN33DDDDD3333D4Z8"),
            ("ConnectWare Cable Co", "Siddharth Rao", "+1-555-0163", "siddharth@connectware.com", "12 Industrial Park", "Denver", "Colorado", "GSTIN07EEEEE4444E5Z9")
        ]
        supplier_map = {}
        for name, contact, phone, email, addr, city, state, gst in suppliers_data:
            sup = Supplier(
                name=name, contact_person=contact, phone=phone, email=email,
                address=addr, city=city, state=state, gst_number=gst
            )
            db.add(sup)
            db.commit()
            db.refresh(sup)
            supplier_map[name] = sup
        print(f"-> Created {len(supplier_map)} suppliers.")

        print("Seeding Products...")
        products_data = [
            # code, name, desc, category, supplier, purchase, selling, current, min, max, location
            ("PRD-LPT-01", "ThinkPro Business Laptop 15", "Intel Core i7, 16GB RAM, 512GB NVMe SSD", "Electronics & Computing", "TechDistro Global Ltd", 850.00, 1150.00, 25, 5, 50, "Aisle 1 - Bay A"),
            ("PRD-MOU-02", "Wireless Ergonomic Mouse", "2.4GHz rechargeable wireless optical mouse with silent click", "Computer Peripherals", "Apex Peripherals Corp", 18.50, 34.99, 8, 10, 80, "Aisle 2 - Shelf B"),
            ("PRD-KBD-03", "Mechanical RGB Keyboard", "Custom linear switches, hot-swappable with braided cable", "Computer Peripherals", "Apex Peripherals Corp", 45.00, 79.99, 32, 10, 60, "Aisle 2 - Shelf C"),
            ("PRD-MON-04", "UltraSharp 27-inch 4K Monitor", "IPS panel, 99% sRGB color gamut, USB-C hub connectivity", "Electronics & Computing", "TechDistro Global Ltd", 280.00, 399.00, 14, 5, 30, "Aisle 1 - Bay B"),
            ("PRD-CAB-05", "Braided USB-C Cable (2m)", "100W Power Delivery and 10Gbps data transmission", "Cables & Adapters", "ConnectWare Cable Co", 4.20, 12.99, 120, 25, 200, "Aisle 4 - Bin 12"),
            ("PRD-PRN-06", "LaserJet Pro Network Printer", "Duplex monochrome laser printer, 40ppm", "Electronics & Computing", "TechDistro Global Ltd", 210.00, 320.00, 6, 4, 15, "Aisle 1 - Bay C"),
            ("PRD-CHR-07", "Ergonomic Mesh Office Chair", "High-back lumbar support, 3D armrests, breathable mesh", "Office Furniture", "Ergonomics World Inc", 140.00, 249.99, 18, 5, 40, "Warehouse Section D"),
            ("PRD-NTB-08", "Hardcover Executive Notebook", "A5 dotted 120gsm acid-free journal with pen holder", "Office Supplies & Stationery", "Prime Office Supplies", 5.50, 14.50, 65, 15, 100, "Aisle 3 - Shelf A"),
            ("PRD-PEN-09", "Gel Ink Rollerball Pen (Pack of 12)", "0.5mm precision quick-dry black ink pens", "Office Supplies & Stationery", "Prime Office Supplies", 6.00, 15.00, 48, 20, 150, "Aisle 3 - Shelf B"),
            ("PRD-LMP-10", "LED Architect Desk Lamp", "Dimmable multi-angle desk lamp with wireless charging base", "Office Furniture", "Ergonomics World Inc", 22.00, 45.00, 4, 8, 35, "Aisle 2 - Shelf D"),
            ("PRD-SSD-11", "External Portable SSD 1TB", "USB 3.2 Gen 2 rugged high-speed solid state drive", "Electronics & Computing", "TechDistro Global Ltd", 65.00, 109.99, 0, 10, 50, "Aisle 1 - Secure Cabinet"),
            ("PRD-HDM-12", "High-Speed 4K HDMI Cable (3m)", "HDMI 2.1 48Gbps ultra certified gold-plated connectors", "Cables & Adapters", "ConnectWare Cable Co", 5.50, 16.99, 85, 20, 150, "Aisle 4 - Bin 15"),
            ("PRD-DSK-13", "Dual-Motor Electric Standing Desk", "Height adjustable 140x70cm oak desktop with anti-collision", "Office Furniture", "Ergonomics World Inc", 260.00, 449.00, 7, 3, 20, "Warehouse Section E"),
            ("PRD-CAM-14", "Full HD 1080p Pro Webcam", "Stereo noise-reducing microphones and privacy shutter", "Computer Peripherals", "Apex Peripherals Corp", 28.00, 54.99, 2, 6, 40, "Aisle 2 - Shelf A")
        ]

        products_list = []
        for code, name, desc, cat_name, sup_name, p_price, s_price, stock, min_s, max_s, loc in products_data:
            cat = category_map[cat_name]
            sup = supplier_map[sup_name]
            p = Product(
                product_code=code,
                name=name,
                description=desc,
                category_id=cat.id,
                supplier_id=sup.id,
                purchase_price=p_price,
                selling_price=s_price,
                current_stock=stock,
                minimum_stock=min_s,
                maximum_stock=max_s,
                location=loc
            )
            db.add(p)
            db.commit()
            db.refresh(p)
            products_list.append(p)
        print(f"-> Created {len(products_list)} products.")

        print("Seeding 25+ realistic Transactions over recent days...")
        now = datetime.now(timezone.utc)
        # Seed realistic transactions to show trend line and logs
        tx_data = [
            # (product_idx, user, type, qty, prev, new, ref, notes, days_ago)
            (0, admin, "STOCK_IN", 30, 0, 30, "INV-2026-001", "Initial bulk order for Q1", 6),
            (0, staff1, "STOCK_OUT", 5, 30, 25, "SO-2026-101", "Issued to Engineering Department", 5),
            (1, admin, "STOCK_IN", 50, 0, 50, "INV-2026-002", "Supplier shipment batch #44", 6),
            (1, staff2, "STOCK_OUT", 22, 50, 28, "SO-2026-102", "New developer workstation setup", 4),
            (1, staff1, "STOCK_OUT", 20, 28, 8, "SO-2026-103", "IT peripheral replacement stock", 1),
            (2, admin, "STOCK_IN", 40, 0, 40, "INV-2026-003", "Mechanical keyboard stock arrival", 6),
            (2, staff2, "STOCK_OUT", 8, 40, 32, "SO-2026-104", "Customer fulfillment order #891", 3),
            (3, admin, "STOCK_IN", 20, 0, 20, "INV-2026-004", "Monitors received from distributor", 5),
            (3, staff1, "STOCK_OUT", 6, 20, 14, "SO-2026-105", "Design studio upgrade delivery", 2),
            (4, admin, "STOCK_IN", 150, 0, 150, "INV-2026-005", "Bulk cable shipment", 6),
            (4, staff2, "STOCK_OUT", 30, 150, 120, "SO-2026-106", "Retail store restock batch", 2),
            (5, admin, "STOCK_IN", 8, 0, 8, "INV-2026-006", "Laser printer inventory intake", 5),
            (5, staff1, "STOCK_OUT", 2, 8, 6, "SO-2026-107", "Administration office installation", 1),
            (6, admin, "STOCK_IN", 25, 0, 25, "INV-2026-007", "Warehouse pallet delivery", 6),
            (6, staff2, "STOCK_OUT", 7, 25, 18, "SO-2026-108", "Corporate customer sales order", 3),
            (7, admin, "STOCK_IN", 80, 0, 80, "INV-2026-008", "Office stationery seasonal intake", 5),
            (7, staff1, "STOCK_OUT", 15, 80, 65, "SO-2026-109", "Supplied to marketing team", 2),
            (8, admin, "STOCK_IN", 60, 0, 60, "INV-2026-009", "Box of gel pens delivery", 4),
            (8, staff2, "STOCK_OUT", 12, 60, 48, "SO-2026-110", "Quarterly stationery supply distribution", 2),
            (9, admin, "STOCK_IN", 15, 0, 15, "INV-2026-010", "Desk lamp crate shipment", 4),
            (9, staff1, "STOCK_OUT", 11, 15, 4, "SO-2026-111", "Executive floor lighting installation", 1),
            (10, admin, "STOCK_IN", 20, 0, 20, "INV-2026-011", "External SSD stock intake", 6),
            (10, staff2, "STOCK_OUT", 20, 20, 0, "SO-2026-112", "Emergency video production project issue", 1),
            (11, admin, "STOCK_IN", 100, 0, 100, "INV-2026-012", "Cables restock shipment", 4),
            (11, staff1, "STOCK_OUT", 15, 100, 85, "SO-2026-113", "Conference room AV installation", 1),
            (12, admin, "STOCK_IN", 10, 0, 10, "INV-2026-013", "Standing desks warehouse intake", 5),
            (12, staff2, "STOCK_OUT", 3, 10, 7, "SO-2026-114", "Remote employee equipment stipend", 2),
            (13, admin, "STOCK_IN", 15, 0, 15, "INV-2026-014", "Webcam shipment arrival", 5),
            (13, staff1, "STOCK_OUT", 13, 15, 2, "SO-2026-115", "Distributed for hybrid remote setup", 0)
        ]

        for p_idx, usr, t_type, qty, prev, new_s, ref, notes, d_ago in tx_data:
            prod = products_list[p_idx]
            price = prod.purchase_price if t_type == "STOCK_IN" else prod.selling_price
            tx = Transaction(
                product_id=prod.id,
                user_id=usr.id,
                transaction_type=t_type,
                quantity=qty,
                previous_stock=prev,
                new_stock=new_s,
                unit_price=price,
                reference_number=ref,
                notes=notes,
                created_at=now - timedelta(days=d_ago, hours=p_idx % 12, minutes=p_idx * 3)
            )
            db.add(tx)

        db.commit()
        print(f"-> Seeded {len(tx_data)} transactions across the past 7 days.")
        print("\n=== DATABASE SEED COMPLETED SUCCESSFULLY ===")
        print(f"Admin Account: admin@stockflow.com | Password: Admin@123")
        print(f"Staff Account 1: john@stockflow.com | Password: Staff@123")
        print(f"Staff Account 2: sarah@stockflow.com | Password: Staff@123")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
