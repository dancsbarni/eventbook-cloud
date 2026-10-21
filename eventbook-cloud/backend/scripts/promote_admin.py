import sys
from app import app, db, User

if len(sys.argv) != 2:
    raise SystemExit("Használat: python scripts/promote_admin.py email@example.com")

email = sys.argv[1].strip().lower()
with app.app_context():
    user = User.query.filter_by(email=email).first()
    if not user:
        raise SystemExit("Nem található ilyen felhasználó. Először regisztrálj a weboldalon.")
    user.role = "admin"
    db.session.commit()
    print(f"Admin jogosultság beállítva: {user.email}")
