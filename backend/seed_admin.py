from backend.core.database import SessionLocal
from backend.models.user import User
from backend.core.security import get_password_hash

def seed_admin():
    db = SessionLocal()
    try:
        admin_email = "admin@example.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if not existing_admin:
            print(f"Creating admin user: {admin_email}")
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                full_name="System Admin",
                role="super_admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
            if existing_admin.role != "super_admin":
                print("Updating existing admin role to super_admin")
                existing_admin.role = "super_admin"
                db.commit()
                
    except Exception as e:
        print(f"Error seeding admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
