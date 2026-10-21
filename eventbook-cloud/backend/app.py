import io
import os
import secrets
from datetime import datetime, timezone
from functools import wraps

import boto3
import qrcode
from flask import Flask, jsonify, request, session, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    category = db.Column(db.String(80), nullable=False, default="Egyéb")
    location = db.Column(db.String(180), nullable=False)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    image_key = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="published")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ticket_types = db.relationship("TicketType", backref="event", cascade="all, delete-orphan", lazy=True)


class TicketType(db.Model):
    __tablename__ = "ticket_types"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    price_huf = db.Column(db.Integer, nullable=False, default=0)
    capacity = db.Column(db.Integer, nullable=False)
    reserved = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (
        CheckConstraint("price_huf >= 0", name="ck_ticket_price_nonnegative"),
        CheckConstraint("capacity >= 0", name="ck_ticket_capacity_nonnegative"),
        CheckConstraint("reserved >= 0 AND reserved <= capacity", name="ck_ticket_reserved_range"),
    )


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    booking_code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="confirmed")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User")
    items = db.relationship("BookingItem", backref="booking", cascade="all, delete-orphan", lazy=True)


class BookingItem(db.Model):
    __tablename__ = "booking_items"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey("ticket_types.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price_huf = db.Column(db.Integer, nullable=False)
    ticket_type = db.relationship("TicketType")


def serialize_ticket_type(t):
    return {
        "id": t.id, "name": t.name, "price_huf": t.price_huf,
        "capacity": t.capacity, "available": max(0, t.capacity - t.reserved)
    }


def serialize_event(e):
    return {
        "id": e.id, "title": e.title, "description": e.description,
        "category": e.category, "location": e.location,
        "start_time": e.start_time.isoformat(), "image_url": e.image_url,
        "status": e.status, "ticket_types": [serialize_ticket_type(t) for t in e.ticket_types]
    }


def serialize_booking(b):
    total = sum(item.quantity * item.unit_price_huf for item in b.items)
    return {
        "id": b.id, "booking_code": b.booking_code, "status": b.status,
        "created_at": b.created_at.isoformat(), "total_huf": total,
        "items": [{
            "ticket_type": item.ticket_type.name,
            "event_title": item.ticket_type.event.title,
            "quantity": item.quantity, "unit_price_huf": item.unit_price_huf,
        } for item in b.items]
    }


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify(error="Bejelentkezés szükséges."), 401
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify(error="Bejelentkezés szükséges."), 401
        if user.role != "admin":
            return jsonify(error="Ehhez admin jogosultság szükséges."), 403
        return fn(*args, **kwargs)
    return wrapper


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///eventbook-dev.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    db.init_app(app)
    CORS(app, supports_credentials=True, origins=os.getenv("FRONTEND_ORIGIN", "http://localhost:8080"))

    with app.app_context():
        db.create_all()
        if Event.query.count() == 0:
            from datetime import timedelta
            demo_events = [
                Event(title="Partyrock XXL", description="A legnagyobb slágerek, felejthetetlen hangulat és egész estés buli.",
                      category="Party", location="Kecskemét", start_time=datetime.now(timezone.utc) + timedelta(days=14),
                      image_url="https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1200&q=80"),
                Event(title="Summer Beats Festival", description="Elektronikus zene, szabadtéri színpad és nyári hangulat.",
                      category="Fesztivál", location="Budapest", start_time=datetime.now(timezone.utc) + timedelta(days=30),
                      image_url="https://images.unsplash.com/photo-1459749411175-04bf5292ceea?auto=format&fit=crop&w=1200&q=80"),
                Event(title="Live Music Night", description="Élőzene és különleges koncertélmény.",
                      category="Koncert", location="Szeged", start_time=datetime.now(timezone.utc) + timedelta(days=45),
                      image_url="https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=1200&q=80"),
            ]
            for event in demo_events:
                event.ticket_types = [
                    TicketType(name="Early Bird", price_huf=2990, capacity=100, reserved=0),
                    TicketType(name="Normál", price_huf=4490, capacity=300, reserved=0),
                ]
                db.session.add(event)
            db.session.commit()

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="eventbook-api")

    @app.get("/api/me")
    def me():
        user = current_user()
        if not user:
            return jsonify(user=None)
        return jsonify(user={"id": user.id, "name": user.name, "email": user.email, "role": user.role})

    @app.post("/api/auth/register")
    def register():
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if len(name) < 2 or "@" not in email or len(password) < 8:
            return jsonify(error="Adj meg nevet, érvényes e-mail-címet és legalább 8 karakteres jelszót."), 400
        user = User(name=name, email=email, password_hash=generate_password_hash(password), role="user")
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Ezzel az e-mail-címmel már létezik fiók."), 409
        session.clear()
        session["user_id"] = user.id
        return jsonify(user={"id": user.id, "name": user.name, "email": user.email, "role": user.role}), 201

    @app.post("/api/auth/login")
    def login():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify(error="Hibás e-mail-cím vagy jelszó."), 401
        session.clear()
        session["user_id"] = user.id
        return jsonify(user={"id": user.id, "name": user.name, "email": user.email, "role": user.role})

    @app.post("/api/auth/logout")
    def logout():
        session.clear()
        return jsonify(message="Sikeres kijelentkezés.")

    @app.get("/api/events")
    def list_events():
        query = Event.query.filter_by(status="published").order_by(Event.start_time.asc())
        category = request.args.get("category")
        search = request.args.get("q", "").strip()
        if category:
            query = query.filter_by(category=category)
        if search:
            like = f"%{search}%"
            query = query.filter(db.or_(Event.title.ilike(like), Event.location.ilike(like), Event.description.ilike(like)))
        return jsonify(events=[serialize_event(e) for e in query.all()])

    @app.get("/api/events/<int:event_id>")
    def event_detail(event_id):
        event = db.session.get(Event, event_id)
        if not event or event.status != "published":
            return jsonify(error="A rendezvény nem található."), 404
        return jsonify(event=serialize_event(event))

    @app.post("/api/events")
    @admin_required
    def create_event():
        data = request.get_json(silent=True) or {}
        required = ["title", "location", "start_time"]
        if any(not str(data.get(k, "")).strip() for k in required):
            return jsonify(error="A cím, helyszín és kezdési idő kötelező."), 400
        try:
            start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
            tickets = data.get("ticket_types") or [{"name": "Normál", "price_huf": 0, "capacity": 100}]
            event = Event(
                title=data["title"].strip(), description=data.get("description", ""),
                category=data.get("category", "Egyéb"), location=data["location"].strip(),
                start_time=start_time, image_url=data.get("image_url"), status="published"
            )
            for t in tickets:
                price, capacity = int(t.get("price_huf", 0)), int(t.get("capacity", 0))
                if price < 0 or capacity < 1:
                    return jsonify(error="A jegyár nem lehet negatív, a kapacitás legalább 1 legyen."), 400
                event.ticket_types.append(TicketType(name=t.get("name", "Normál"), price_huf=price, capacity=capacity))
            db.session.add(event)
            db.session.commit()
            return jsonify(event=serialize_event(event)), 201
        except (ValueError, TypeError):
            db.session.rollback()
            return jsonify(error="Hibás dátum, ár vagy kapacitás."), 400

    @app.put("/api/events/<int:event_id>")
    @admin_required
    def update_event(event_id):
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify(error="A rendezvény nem található."), 404
        data = request.get_json(silent=True) or {}
        for field in ("title", "description", "category", "location", "image_url", "status"):
            if field in data:
                setattr(event, field, data[field])
        if "start_time" in data:
            try:
                event.start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
            except ValueError:
                return jsonify(error="Hibás dátum."), 400
        db.session.commit()
        return jsonify(event=serialize_event(event))

    @app.delete("/api/events/<int:event_id>")
    @admin_required
    def delete_event(event_id):
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify(error="A rendezvény nem található."), 404
        # Keep historical booking references; hide event instead of hard-deleting it.
        event.status = "archived"
        db.session.commit()
        return jsonify(message="Rendezvény archiválva.")

    @app.post("/api/bookings")
    @login_required
    def create_booking():
        user = current_user()
        data = request.get_json(silent=True) or {}
        items = data.get("items") or []
        if not items:
            return jsonify(error="Legalább egy jegyet ki kell választani."), 400
        try:
            booking = Booking(user_id=user.id, booking_code=secrets.token_urlsafe(12))
            db.session.add(booking)
            for item in items:
                ticket_id = int(item.get("ticket_type_id"))
                quantity = int(item.get("quantity", 0))
                if quantity < 1 or quantity > 10:
                    db.session.rollback()
                    return jsonify(error="Egy foglalásban 1–10 jegy választható típusonként."), 400
                ticket = db.session.execute(
                    select(TicketType).where(TicketType.id == ticket_id).with_for_update()
                ).scalar_one_or_none()
                if not ticket or ticket.event.status != "published":
                    db.session.rollback()
                    return jsonify(error="A kiválasztott jegytípus nem érhető el."), 404
                if ticket.capacity - ticket.reserved < quantity:
                    db.session.rollback()
                    return jsonify(error=f"Nincs elegendő szabad jegy: {ticket.name}."), 409
                ticket.reserved += quantity
                booking.items.append(BookingItem(ticket_type=ticket, quantity=quantity, unit_price_huf=ticket.price_huf))
            db.session.commit()
            return jsonify(booking=serialize_booking(booking)), 201
        except (ValueError, TypeError):
            db.session.rollback()
            return jsonify(error="Hibás jegyadat."), 400

    @app.get("/api/bookings")
    @login_required
    def my_bookings():
        user = current_user()
        bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
        return jsonify(bookings=[serialize_booking(b) for b in bookings])

    @app.get("/api/bookings/<booking_code>/qr")
    @login_required
    def booking_qr(booking_code):
        user = current_user()
        booking = Booking.query.filter_by(booking_code=booking_code, user_id=user.id).first()
        if not booking:
            return jsonify(error="A foglalás nem található."), 404
        qr = qrcode.QRCode(box_size=8, border=3)
        qr.add_data(f"EVENTBOOK:{booking.booking_code}")
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return send_file(output, mimetype="image/png", download_name=f"{booking.booking_code}.png")

    @app.get("/api/admin/stats")
    @admin_required
    def admin_stats():
        events = Event.query.filter_by(status="published").all()
        bookings = Booking.query.filter_by(status="confirmed").all()
        sold = sum(item.quantity for b in bookings for item in b.items)
        revenue = sum(item.quantity * item.unit_price_huf for b in bookings for item in b.items)
        return jsonify(events=len(events), bookings=len(bookings), tickets_sold=sold, booking_value_huf=revenue)

    @app.get("/api/admin/bookings")
    @admin_required
    def admin_bookings():
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        return jsonify(bookings=[{
            **serialize_booking(b), "customer_name": b.user.name, "customer_email": b.user.email
        } for b in bookings])

    @app.post("/api/admin/events/<int:event_id>/poster")
    @admin_required
    def upload_poster(event_id):
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify(error="A rendezvény nem található."), 404
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return jsonify(error="Válassz ki egy képfájlt."), 400
        if uploaded.mimetype not in {"image/jpeg", "image/png", "image/webp"}:
            return jsonify(error="Csak JPG, PNG vagy WebP kép tölthető fel."), 400
        bucket = os.getenv("S3_BUCKET", "").strip()
        if not bucket:
            return jsonify(error="Az S3_BUCKET nincs beállítva; az S3-feltöltést később konfiguráljuk."), 503
        key = f"event-posters/{event.id}/{secrets.token_hex(8)}-{os.path.basename(uploaded.filename)}"
        try:
            boto3.client("s3", region_name=os.getenv("AWS_REGION", "eu-central-1")).upload_fileobj(
                uploaded, bucket, key, ExtraArgs={"ContentType": uploaded.mimetype}
            )
            event.image_key = key
            db.session.commit()
            return jsonify(message="Plakát feltöltve S3-ba.", image_key=key)
        except Exception:
            db.session.rollback()
            app.logger.exception("S3 upload failed")
            return jsonify(error="Az S3-feltöltés nem sikerült. Ellenőrizd az IAM-szerepkört és a bucket beállítását."), 502

    return app


app = create_app()
