"""
Web Admin Panel Routes (Jinja2 + HTMX).
Serves HTML pages for managing residential gate data.
"""

import os
import hashlib
import secrets
import csv
import io
from fastapi import APIRouter, Request, Cookie, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader
from bson import ObjectId
from datetime import datetime
import re

from drivers.mongo.connection import Mongo

_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    autoescape=True,
)

router = APIRouter(prefix="/admin", tags=["web"])

_mongo = None
_sessions = {}  # fallback in-memory


def hash_password(password: str) -> str:
    """Simple SHA256 hash for passwords."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_current_user(session_token: str = None) -> dict:
    """Get current logged-in user from session token. Check DB first, fallback to memory."""
    if not session_token:
        return None
    # Check in-memory first (fast)
    if session_token in _sessions:
        return _sessions[session_token]
    # Check MongoDB (persists across restarts)
    db = get_db()
    session = db.sessions.find_one({"token": session_token})
    if session:
        user_data = {"username": session["username"], "role": session.get("role", "admin"), "name": session.get("name", "")}
        _sessions[session_token] = user_data  # cache in memory
        return user_data
    return None


def get_db():
    global _mongo
    if _mongo is None:
        _mongo = Mongo()
    return _mongo.get_db()


def render(template_name: str, **kwargs) -> HTMLResponse:
    template = _env.get_template(template_name)
    html = template.render(**kwargs)
    return HTMLResponse(content=html)


def require_auth(request: Request):
    """Check if user is logged in. Returns user dict or None."""
    token = request.cookies.get("session_token")
    return get_current_user(token)


def _parse_members(form) -> list:
    """Parse member_name[], member_relation[], etc from form data into list of dicts."""
    names = form.getlist("member_name[]")
    relations = form.getlist("member_relation[]")
    phones = form.getlist("member_phone[]")
    id_numbers = form.getlist("member_id_number[]")
    members = []
    for i, name in enumerate(names):
        if not name.strip():
            continue
        members.append({
            "name": name.strip(),
            "relation": relations[i] if i < len(relations) else "other",
            "phone": phones[i].strip() if i < len(phones) else "",
            "id_number": id_numbers[i].strip() if i < len(id_numbers) else "",
            "is_active": True,
        })
    return members


PER_PAGE = 20


def paginate(request: Request, collection, query={}, sort=None, per_page=PER_PAGE):
    """Helper: paginate a mongo collection query."""
    page = int(request.query_params.get("page", 1))
    if page < 1:
        page = 1
    total = collection.count_documents(query)
    total_pages = max(1, (total + per_page - 1) // per_page)
    cursor = collection.find(query)
    if sort:
        cursor = cursor.sort(sort)
    items = list(cursor.skip((page - 1) * per_page).limit(per_page))
    return items, page, total_pages, total


# ==================== AUTH ROUTES ====================

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = require_auth(request)
    if user:
        return RedirectResponse(url="/admin/", status_code=303)
    return render("login.html", error=None, username="")


@router.post("/login")
def login_submit(request: Request, username: str = Form(""), password: str = Form("")):
    db = get_db()
    admin = db.admins.find_one({"username": username, "is_active": True})
    if not admin or admin.get("password_hash") != hash_password(password):
        return render("login.html", error="Invalid username or password", username=username)

    # Create session
    token = secrets.token_hex(32)
    session_data = {"username": admin["username"], "role": admin.get("role", "admin"), "name": admin.get("name", "")}
    _sessions[token] = session_data

    # Persist session to MongoDB
    db.sessions.update_one(
        {"token": token},
        {"$set": {"token": token, **session_data, "created_at": datetime.utcnow()}},
        upsert=True,
    )

    # Update last login
    db.admins.update_one({"_id": admin["_id"]}, {"$set": {"last_login_at": datetime.utcnow()}})

    response = RedirectResponse(url="/admin/", status_code=303)
    response.set_cookie(key="session_token", value=token, httponly=True, max_age=86400)
    return response


@router.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        _sessions.pop(token, None)
        db = get_db()
        db.sessions.delete_one({"token": token})
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("session_token")
    return response


# ==================== DASHBOARD ====================

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    stats = {
        "houses": db.houses.count_documents({}),
        "families": db.families.count_documents({"status": "active"}),
        "vehicles": db.vehicles.count_documents({"is_active": True}),
        "guests_inside": db.guests.count_documents({"status": "inside"}),
        "rfid_cards": db.rfid_cards.count_documents({"is_active": True}),
        "dues_unpaid": db.dues.count_documents({"status": {"$in": ["unpaid", "overdue"]}}),
    }
    recent_logs = list(db.access_logs.find().sort("timestamp", -1).limit(10))
    return render("dashboard.html", stats=stats, recent_logs=recent_logs)


@router.get("/houses", response_class=HTMLResponse)
def houses_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.house.interface import house_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    houses, page, total_pages, total = house_usecase.list(search=search or None, page=page, per_page=per_page)
    return render("houses/list.html",
        houses=[{"_id": h.id, **house_usecase.serialize(h)} for h in houses],
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/houses", export_url="/admin/export/houses", search=search)


@router.get("/vehicles", response_class=HTMLResponse)
def vehicles_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.vehicle.interface import vehicle_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    vehicles, page, total_pages, total = vehicle_usecase.list(search=search or None, page=page, per_page=per_page)
    return render("vehicles/list.html",
        vehicles=[{"_id": v.id, **vehicle_usecase.serialize(v)} for v in vehicles],
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/vehicles", export_url="/admin/export/vehicles", search=search)


@router.get("/families", response_class=HTMLResponse)
def families_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.family.interface import family_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    families, page, total_pages, total = family_usecase.list(search=search or None, page=page, per_page=per_page)
    return render("families/list.html",
        families=[{"_id": f.id, **family_usecase.serialize(f)} for f in families],
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/families", export_url="/admin/export/families", search=search)


@router.get("/guests", response_class=HTMLResponse)
def guests_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.guest.interface import guest_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    guests, page, total_pages, total = guest_usecase.list(search=search or None, page=page, per_page=per_page)
    return render("guests/list.html",
        guests=[{"_id": g.id, **guest_usecase.serialize(g)} for g in guests],
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/guests", export_url="/admin/export/guests", search=search)


@router.get("/rfid", response_class=HTMLResponse)
def rfid_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.rfid_card.interface import rfid_card_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    cards, page, total_pages, total = rfid_card_usecase.list(search=search or None, page=page, per_page=per_page)
    return render("rfid/list.html",
        cards=[{"_id": c.id, **rfid_card_usecase.serialize(c)} for c in cards],
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/rfid", export_url="/admin/export/rfid", search=search)


@router.get("/dues", response_class=HTMLResponse)
def dues_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.due.interface import due_usecase
    from usecases.family.interface import family_usecase
    from usecases.house.interface import house_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    status_filter = request.query_params.get("status", "").strip()
    month_filter = request.query_params.get("month", "").strip()  # format: YYYY-MM
    family_filter = request.query_params.get("family_id", "").strip()
    block_filter = request.query_params.get("block", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    # Parse month filter
    filter_year, filter_month = None, None
    if month_filter and "-" in month_filter:
        parts = month_filter.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            filter_year, filter_month = int(parts[0]), int(parts[1])
    # If block filter, resolve family_ids in that block
    family_ids_in_block = None
    if block_filter:
        from bson import ObjectId as _OID
        db = get_db()
        house_ids = [h["_id"] for h in db.houses.find({"block": block_filter}, {"_id": 1})]
        if house_ids:
            family_ids_in_block = [str(f["_id"]) for f in db.families.find({"houseId": {"$in": [str(h) for h in house_ids]}}, {"_id": 1})]
        else:
            family_ids_in_block = []
    dues, page, total_pages, total = due_usecase.list(
        search=search or None, status=status_filter or None,
        year=filter_year, month=filter_month,
        family_id=family_filter or None,
        family_ids=family_ids_in_block,
        page=page, per_page=per_page,
    )
    dues_data = [{"_id": d.id, **due_usecase.serialize(d)} for d in dues]
    dues_data = due_usecase.enrich_with_family(dues_data)
    # Get families and blocks for filter dropdowns
    families, _, _, _ = family_usecase.list(page=1, per_page=200)
    families_list = [{"_id": f.id, "head_name": f.head_name} for f in families]
    db = get_db()
    blocks = sorted(set(h.get("block", "") for h in db.houses.find({}, {"block": 1}) if h.get("block")))
    return render("dues/list.html",
        dues=dues_data,
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/dues", export_url="/admin/export/dues",
        search=search, status_filter=status_filter, month_filter=month_filter,
        family_filter=family_filter, block_filter=block_filter,
        families=families_list, blocks=blocks)


@router.get("/events", response_class=HTMLResponse)
def events_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.event.interface import event_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    events, page, total_pages, total = event_usecase.list(search=search or None, page=page, per_page=per_page)
    return render("events/list.html",
        events=[{"_id": e.id, **event_usecase.serialize(e)} for e in events],
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/events", export_url="/admin/export/events", search=search)


@router.get("/settings", response_class=HTMLResponse)
def settings_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.setting.interface import setting_usecase
    settings = setting_usecase.list()
    return render("settings/list.html",
        settings=[{"_id": s.id, **setting_usecase.serialize(s)} for s in settings])


@router.get("/access-logs", response_class=HTMLResponse)
def access_logs_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.access_log.interface import access_log_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    per_page = int(request.query_params.get("per_page", PER_PAGE))
    if per_page not in (10, 20, 50, 100):
        per_page = PER_PAGE
    logs, page, total_pages, total = access_log_usecase.list(search=search or None, page=page, per_page=per_page)
    return render("access_logs/list.html",
        logs=[{"_id": l.id, **access_log_usecase.serialize(l)} for l in logs],
        page=page, total_pages=total_pages, total=total, per_page=per_page,
        base_url="/admin/access-logs", export_url="/admin/export/access-logs", search=search)


# --- CRUD Routes ---
# NOTE: /create routes MUST be defined BEFORE /{id} routes to avoid FastAPI matching "create" as an id.


# ==================== HOUSES CRUD ====================

@router.get("/houses/create", response_class=HTMLResponse)
def houses_create_form(request: Request):
    return render("houses/form.html", house=None)


@router.post("/houses/create")
def houses_create(
    request: Request,
    block: str = Form(""),
    street: str = Form(""),
    house_number: str = Form(""),
    status: str = Form("vacant"),
    address_note: str = Form(""),
):
    from usecases.house.interface import house_usecase
    house_usecase.create(
        block=block, house_number=house_number, street=street,
        status=status, address_note=address_note,
    )
    return RedirectResponse(url="/admin/houses?msg=House+created+successfully", status_code=303)


@router.get("/houses/{id}", response_class=HTMLResponse)
def houses_edit_form(request: Request, id: str):
    from usecases.house.interface import house_usecase
    house = house_usecase.find_by_id(id)
    if not house:
        return RedirectResponse(url="/admin/houses", status_code=303)
    return render("houses/form.html", house={"_id": house.id, **house_usecase.serialize(house)})


@router.post("/houses/{id}")
def houses_update(
    request: Request,
    id: str,
    block: str = Form(""),
    street: str = Form(""),
    house_number: str = Form(""),
    status: str = Form(""),
    address_note: str = Form(""),
):
    from usecases.house.interface import house_usecase
    house_usecase.update(
        house_id=id, block=block, house_number=house_number,
        street=street, status=status, address_note=address_note,
    )
    return RedirectResponse(url="/admin/houses?msg=House+updated+successfully", status_code=303)


@router.post("/houses/{id}/delete")
def houses_delete(request: Request, id: str):
    from usecases.house.interface import house_usecase
    house_usecase.delete(id)
    return RedirectResponse(url="/admin/houses?msg=House+deleted", status_code=303)


# ==================== VEHICLES CRUD ====================

@router.get("/vehicles/create", response_class=HTMLResponse)
def vehicles_create_form(request: Request):
    from usecases.family.interface import family_usecase
    families, _, _, _ = family_usecase.list(page=1, per_page=200)
    return render("vehicles/form.html", vehicle=None, families=[{"_id": f.id, "head_name": f.head_name} for f in families])


@router.post("/vehicles/create")
def vehicles_create(
    request: Request,
    plate_number: str = Form(""),
    type: str = Form("car"),
    brand: str = Form(""),
    model: str = Form(""),
    color: str = Form(""),
    year: str = Form(""),
    family_id: str = Form(""),
    is_active: str = Form(""),
):
    from usecases.vehicle.interface import vehicle_usecase
    vehicle_usecase.create(
        plate_number=plate_number, type=type, brand=brand, model=model,
        color=color, year=int(year) if year.isdigit() else 0,
        is_active=is_active == "true", family_id=family_id,
    )
    return RedirectResponse(url="/admin/vehicles?msg=Vehicle+saved", status_code=303)


@router.get("/vehicles/{id}", response_class=HTMLResponse)
def vehicles_edit_form(request: Request, id: str):
    from usecases.vehicle.interface import vehicle_usecase
    from usecases.family.interface import family_usecase
    vehicle = vehicle_usecase.find_by_id(id)
    if not vehicle:
        return RedirectResponse(url="/admin/vehicles?msg=Vehicle+saved", status_code=303)
    families, _, _, _ = family_usecase.list(page=1, per_page=200)
    return render("vehicles/form.html", vehicle={"_id": vehicle.id, **vehicle_usecase.serialize(vehicle)}, families=[{"_id": f.id, "head_name": f.head_name} for f in families])


@router.post("/vehicles/{id}")
def vehicles_update(
    request: Request,
    id: str,
    plate_number: str = Form(""),
    type: str = Form("car"),
    brand: str = Form(""),
    model: str = Form(""),
    color: str = Form(""),
    year: str = Form(""),
    family_id: str = Form(""),
    is_active: str = Form(""),
):
    from usecases.vehicle.interface import vehicle_usecase
    vehicle_usecase.update(
        vehicle_id=id, plate_number=plate_number, type=type, brand=brand,
        model=model, color=color, year=int(year) if year.isdigit() else 0,
        is_active=is_active == "true", family_id=family_id,
    )
    return RedirectResponse(url="/admin/vehicles?msg=Vehicle+saved", status_code=303)


@router.post("/vehicles/{id}/delete")
def vehicles_delete(request: Request, id: str):
    from usecases.vehicle.interface import vehicle_usecase
    vehicle_usecase.delete(id)
    return RedirectResponse(url="/admin/vehicles?msg=Vehicle+saved", status_code=303)


# ==================== FAMILIES CRUD ====================

@router.get("/families/create", response_class=HTMLResponse)
def families_create_form(request: Request):
    from usecases.house.interface import house_usecase
    houses, _, _, _ = house_usecase.list(page=1, per_page=200)
    return render("families/form.html", family=None, houses=[{"_id": h.id, "block": h.block, "house_number": h.house_number} for h in houses])


@router.post("/families/create")
async def families_create(request: Request):
    from usecases.family.interface import family_usecase
    form = await request.form()
    members = _parse_members(form)
    family_usecase.create(
        head_name=form.get("head_name", ""),
        head_phone=form.get("head_phone", ""),
        head_id_number=form.get("head_id_number", ""),
        house_id=form.get("house_id", ""),
        total_members=len(members) + 1,
        status=form.get("status", "active"),
        members=members,
    )
    return RedirectResponse(url="/admin/families?msg=Family+saved", status_code=303)


@router.get("/families/{id}", response_class=HTMLResponse)
def families_edit_form(request: Request, id: str):
    from usecases.family.interface import family_usecase
    from usecases.house.interface import house_usecase
    family = family_usecase.find_by_id(id)
    if not family:
        return RedirectResponse(url="/admin/families?msg=Family+saved", status_code=303)
    houses, _, _, _ = house_usecase.list(page=1, per_page=200)
    return render("families/form.html", family={"_id": family.id, **family_usecase.serialize(family)}, houses=[{"_id": h.id, "block": h.block, "house_number": h.house_number} for h in houses])


@router.post("/families/{id}")
async def families_update(request: Request, id: str):
    from usecases.family.interface import family_usecase
    form = await request.form()
    members = _parse_members(form)
    family_usecase.update(
        family_id=id,
        head_name=form.get("head_name", ""),
        head_phone=form.get("head_phone", ""),
        head_id_number=form.get("head_id_number", ""),
        house_id=form.get("house_id", ""),
        total_members=len(members) + 1,
        status=form.get("status", "active"),
        members=members,
    )
    return RedirectResponse(url="/admin/families?msg=Family+saved", status_code=303)


@router.post("/families/{id}/delete")
def families_delete(request: Request, id: str):
    from usecases.family.interface import family_usecase
    family_usecase.delete(id)
    return RedirectResponse(url="/admin/families?msg=Family+saved", status_code=303)


# ==================== RFID CARDS CRUD ====================

@router.get("/rfid/create", response_class=HTMLResponse)
def rfid_create_form(request: Request):
    from usecases.family.interface import family_usecase
    families, _, _, _ = family_usecase.list(page=1, per_page=200)
    return render("rfid/form.html", card=None, families=[{"_id": f.id, "head_name": f.head_name} for f in families])


@router.post("/rfid/create")
def rfid_create(
    request: Request,
    card_uid: str = Form(""),
    holder_name: str = Form(""),
    card_type: str = Form("resident"),
    family_id: str = Form(""),
    is_active: str = Form(""),
):
    from usecases.rfid_card.interface import rfid_card_usecase
    rfid_card_usecase.create(
        card_uid=card_uid, holder_name=holder_name, card_type=card_type,
        family_id=family_id, is_active=is_active == "true",
    )
    return RedirectResponse(url="/admin/rfid?msg=RFID+card+saved", status_code=303)


@router.get("/rfid/{id}", response_class=HTMLResponse)
def rfid_edit_form(request: Request, id: str):
    from usecases.rfid_card.interface import rfid_card_usecase
    from usecases.family.interface import family_usecase
    card = rfid_card_usecase.find_by_id(id)
    if not card:
        return RedirectResponse(url="/admin/rfid?msg=RFID+card+saved", status_code=303)
    families, _, _, _ = family_usecase.list(page=1, per_page=200)
    return render("rfid/form.html", card={"_id": card.id, **rfid_card_usecase.serialize(card)}, families=[{"_id": f.id, "head_name": f.head_name} for f in families])


@router.post("/rfid/{id}")
def rfid_update(
    request: Request,
    id: str,
    card_uid: str = Form(""),
    holder_name: str = Form(""),
    card_type: str = Form("resident"),
    family_id: str = Form(""),
    is_active: str = Form(""),
):
    from usecases.rfid_card.interface import rfid_card_usecase
    rfid_card_usecase.update(
        card_id=id, card_uid=card_uid, holder_name=holder_name,
        card_type=card_type, family_id=family_id, is_active=is_active == "true",
    )
    return RedirectResponse(url="/admin/rfid?msg=RFID+card+saved", status_code=303)


@router.post("/rfid/{id}/delete")
def rfid_delete(request: Request, id: str):
    from usecases.rfid_card.interface import rfid_card_usecase
    rfid_card_usecase.delete(id)
    return RedirectResponse(url="/admin/rfid?msg=RFID+card+saved", status_code=303)


# ==================== GUESTS CRUD ====================

@router.get("/guests/create", response_class=HTMLResponse)
def guests_create_form(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.house.interface import house_usecase
    from usecases.setting.interface import setting_usecase
    houses, _, _, _ = house_usecase.list(page=1, per_page=200)
    default_max_hours = setting_usecase.get_value("guest_max_duration_hours", "24")
    return render("guests/form.html", guest=None,
        houses=[{"_id": h.id, "block": h.block, "house_number": h.house_number} for h in houses],
        default_max_hours=int(default_max_hours) if default_max_hours.isdigit() else 24)


@router.post("/guests/create")
def guests_create(
    request: Request,
    guest_name: str = Form(""),
    guest_phone: str = Form(""),
    guest_id_number: str = Form(""),
    purpose: str = Form("visit"),
    vehicle_plate: str = Form(""),
    vehicle_type: str = Form("none"),
    visiting_house_id: str = Form(""),
    approved_by: str = Form("security"),
    notes: str = Form(""),
    max_duration_hours: str = Form("0"),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.guest.interface import guest_usecase
    guest_usecase.create(
        guest_name=guest_name, guest_phone=guest_phone,
        guest_id_number=guest_id_number, purpose=purpose,
        vehicle_plate=vehicle_plate, vehicle_type=vehicle_type,
        visiting_house_id=visiting_house_id, approved_by=approved_by,
        notes=notes,
        max_duration_hours=int(max_duration_hours) if max_duration_hours.isdigit() else 0,
    )
    return RedirectResponse(url="/admin/guests?msg=Guest+registered", status_code=303)


@router.get("/guests/{id}", response_class=HTMLResponse)
def guests_edit_form(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.guest.interface import guest_usecase
    from usecases.house.interface import house_usecase
    from usecases.setting.interface import setting_usecase
    guest = guest_usecase.find_by_id(id)
    if not guest:
        return RedirectResponse(url="/admin/guests", status_code=303)
    houses, _, _, _ = house_usecase.list(page=1, per_page=200)
    default_max_hours = setting_usecase.get_value("guest_max_duration_hours", "24")
    return render("guests/form.html",
        guest={"_id": guest.id, **guest_usecase.serialize(guest)},
        houses=[{"_id": h.id, "block": h.block, "house_number": h.house_number} for h in houses],
        default_max_hours=int(default_max_hours) if default_max_hours.isdigit() else 24)


@router.post("/guests/{id}")
def guests_update(
    request: Request,
    id: str,
    guest_name: str = Form(""),
    guest_phone: str = Form(""),
    guest_id_number: str = Form(""),
    purpose: str = Form("visit"),
    vehicle_plate: str = Form(""),
    vehicle_type: str = Form("none"),
    visiting_house_id: str = Form(""),
    approved_by: str = Form("security"),
    notes: str = Form(""),
    status: str = Form("inside"),
    max_duration_hours: str = Form("0"),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.guest.interface import guest_usecase
    guest_usecase.update(
        guest_id=id, guest_name=guest_name, guest_phone=guest_phone,
        guest_id_number=guest_id_number, purpose=purpose,
        vehicle_plate=vehicle_plate, vehicle_type=vehicle_type,
        visiting_house_id=visiting_house_id, approved_by=approved_by,
        notes=notes, status=status,
        max_duration_hours=int(max_duration_hours) if max_duration_hours.isdigit() else 0,
    )
    return RedirectResponse(url="/admin/guests?msg=Guest+updated", status_code=303)


@router.post("/guests/{id}/checkout")
def guests_checkout(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.guest.interface import guest_usecase
    guest_usecase.checkout(id)
    return RedirectResponse(url="/admin/guests?msg=Guest+checked+out", status_code=303)


@router.post("/guests/{id}/delete")
def guests_delete(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.guest.interface import guest_usecase
    guest_usecase.delete(id)
    return RedirectResponse(url="/admin/guests?msg=Guest+deleted", status_code=303)


# ==================== DUES CRUD ====================

@router.get("/dues/create", response_class=HTMLResponse)
def dues_create_form(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.family.interface import family_usecase
    families, _, _, _ = family_usecase.list(page=1, per_page=200)
    return render("dues/form.html", due=None, families=[{"_id": f.id, "head_name": f.head_name} for f in families])


@router.post("/dues/create")
def dues_create(
    request: Request,
    family_id: str = Form(""),
    period: str = Form(""),
    type: str = Form("monthly"),
    amount: str = Form("0"),
    paid_amount: str = Form("0"),
    status: str = Form("unpaid"),
    payment_method: str = Form(""),
    collector_name: str = Form(""),
    notes: str = Form(""),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.due.interface import due_usecase
    due_usecase.create(
        family_id=family_id, period=period, type=type,
        amount=int(amount) if amount.isdigit() else 0,
        paid_amount=int(paid_amount) if paid_amount.isdigit() else 0,
        status=status, payment_method=payment_method,
        collector_name=collector_name, notes=notes,
    )
    return RedirectResponse(url="/admin/dues?msg=Due+created", status_code=303)


@router.get("/dues/{id}", response_class=HTMLResponse)
def dues_edit_form(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.due.interface import due_usecase
    from usecases.family.interface import family_usecase
    due = due_usecase.find_by_id(id)
    if not due:
        return RedirectResponse(url="/admin/dues", status_code=303)
    families, _, _, _ = family_usecase.list(page=1, per_page=200)
    return render("dues/form.html", due={"_id": due.id, **due_usecase.serialize(due)}, families=[{"_id": f.id, "head_name": f.head_name} for f in families])


@router.post("/dues/{id}")
def dues_update(
    request: Request,
    id: str,
    family_id: str = Form(""),
    period: str = Form(""),
    type: str = Form("monthly"),
    amount: str = Form("0"),
    paid_amount: str = Form("0"),
    status: str = Form("unpaid"),
    payment_method: str = Form(""),
    collector_name: str = Form(""),
    notes: str = Form(""),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.due.interface import due_usecase
    due_usecase.update(
        due_id=id, family_id=family_id, period=period, type=type,
        amount=int(amount) if amount.isdigit() else 0,
        paid_amount=int(paid_amount) if paid_amount.isdigit() else 0,
        status=status, payment_method=payment_method,
        collector_name=collector_name, notes=notes,
    )
    return RedirectResponse(url="/admin/dues?msg=Due+updated", status_code=303)


@router.post("/dues/{id}/delete")
def dues_delete(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.due.interface import due_usecase
    due_usecase.delete(id)
    return RedirectResponse(url="/admin/dues?msg=Due+deleted", status_code=303)


# ==================== EVENTS CRUD ====================

@router.get("/events/create", response_class=HTMLResponse)
def events_create_form(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    return render("events/form.html", event=None)


@router.post("/events/create")
def events_create(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    type: str = Form("announcement"),
    location: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    organizer: str = Form(""),
    target_audience: str = Form("all"),
    is_mandatory: str = Form(""),
    status: str = Form("upcoming"),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.event.interface import event_usecase
    event_usecase.create(
        title=title, description=description, type=type,
        location=location, start_date=start_date, end_date=end_date,
        organizer=organizer, target_audience=target_audience,
        is_mandatory=is_mandatory == "true", status=status,
    )
    return RedirectResponse(url="/admin/events?msg=Event+created", status_code=303)


@router.get("/events/{id}", response_class=HTMLResponse)
def events_edit_form(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.event.interface import event_usecase
    event = event_usecase.find_by_id(id)
    if not event:
        return RedirectResponse(url="/admin/events", status_code=303)
    return render("events/form.html", event={"_id": event.id, **event_usecase.serialize(event)})


@router.post("/events/{id}")
def events_update(
    request: Request,
    id: str,
    title: str = Form(""),
    description: str = Form(""),
    type: str = Form("announcement"),
    location: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    organizer: str = Form(""),
    target_audience: str = Form("all"),
    is_mandatory: str = Form(""),
    status: str = Form("upcoming"),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.event.interface import event_usecase
    event_usecase.update(
        event_id=id, title=title, description=description, type=type,
        location=location, start_date=start_date, end_date=end_date,
        organizer=organizer, target_audience=target_audience,
        is_mandatory=is_mandatory == "true", status=status,
    )
    return RedirectResponse(url="/admin/events?msg=Event+updated", status_code=303)


@router.post("/events/{id}/delete")
def events_delete(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.event.interface import event_usecase
    event_usecase.delete(id)
    return RedirectResponse(url="/admin/events?msg=Event+deleted", status_code=303)


# ==================== SETTINGS CRUD ====================

@router.post("/settings/{id}")
def settings_update_inline(request: Request, id: str, value: str = Form("")):
    """Inline update from list page (backward compat)."""
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.setting.interface import setting_usecase
    setting_usecase.update(id, value=value)
    return RedirectResponse(url="/admin/settings?msg=Setting+updated", status_code=303)


@router.get("/settings/create", response_class=HTMLResponse)
def settings_create_form(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    return render("settings/form.html", setting=None)


@router.post("/settings/create")
def settings_create(
    request: Request,
    key: str = Form(""),
    key_custom: str = Form(""),
    value: str = Form(""),
    category: str = Form("general"),
    description: str = Form(""),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.setting.interface import setting_usecase
    actual_key = key_custom.strip() if key == "__custom__" or not key else key
    if not actual_key:
        return RedirectResponse(url="/admin/settings/create?msg=Key+is+required", status_code=303)
    setting_usecase.create(key=actual_key, value=value, category=category, description=description)
    return RedirectResponse(url="/admin/settings?msg=Setting+created", status_code=303)


@router.get("/settings/{id}/edit", response_class=HTMLResponse)
def settings_edit_form(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.setting.interface import setting_usecase
    setting = setting_usecase.find_by_id(id)
    if not setting:
        return RedirectResponse(url="/admin/settings", status_code=303)
    return render("settings/form.html", setting={"_id": setting.id, **setting_usecase.serialize(setting)})


@router.post("/settings/{id}/edit")
def settings_update_full(
    request: Request,
    id: str,
    key: str = Form(""),
    value: str = Form(""),
    category: str = Form("general"),
    description: str = Form(""),
):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.setting.interface import setting_usecase
    setting_usecase.update(id, key=key, value=value, category=category, description=description)
    return RedirectResponse(url="/admin/settings?msg=Setting+updated", status_code=303)


@router.post("/settings/{id}/delete")
def settings_delete(request: Request, id: str):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.setting.interface import setting_usecase
    setting_usecase.delete(id)
    return RedirectResponse(url="/admin/settings?msg=Setting+deleted", status_code=303)


# ==================== ADMIN USERS CRUD ====================

@router.get("/admins", response_class=HTMLResponse)
def admins_list(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    if user.get("role") != "superadmin":
        return RedirectResponse(url="/admin/", status_code=303)
    from usecases.admin.interface import admin_usecase
    page = int(request.query_params.get("page", 1))
    search = request.query_params.get("q", "").strip()
    admins, page, total_pages, total = admin_usecase.list(search=search or None, page=page)
    return render("admins/list.html",
        admins=[{"_id": a.get("_id"), **admin_usecase.serialize(a)} for a in admins],
        page=page, total_pages=total_pages, total=total, per_page=20,
        base_url="/admin/admins", search=search)


@router.get("/admins/create", response_class=HTMLResponse)
def admins_create_form(request: Request):
    user = require_auth(request)
    if not user or user.get("role") != "superadmin":
        return RedirectResponse(url="/admin/login", status_code=303)
    return render("admins/form.html", admin_user=None)


@router.post("/admins/create")
def admins_create(
    request: Request,
    username: str = Form(""),
    name: str = Form(""),
    password: str = Form(""),
    role: str = Form("admin"),
    is_active: str = Form(""),
):
    user = require_auth(request)
    if not user or user.get("role") != "superadmin":
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.admin.interface import admin_usecase
    result = admin_usecase.create(
        username=username, name=name, password=password,
        role=role, is_active=is_active == "true",
    )
    if result is None:
        return render("admins/form.html", admin_user=None, error="Username already exists")
    return RedirectResponse(url="/admin/admins?msg=Admin+saved", status_code=303)


@router.get("/admins/{id}", response_class=HTMLResponse)
def admins_edit_form(request: Request, id: str):
    user = require_auth(request)
    if not user or user.get("role") != "superadmin":
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.admin.interface import admin_usecase
    admin_user = admin_usecase.find_by_id(id)
    if not admin_user:
        return RedirectResponse(url="/admin/admins?msg=Admin+saved", status_code=303)
    return render("admins/form.html", admin_user={"_id": admin_user.get("_id"), **admin_usecase.serialize(admin_user)})


@router.post("/admins/{id}")
def admins_update(
    request: Request,
    id: str,
    username: str = Form(""),
    name: str = Form(""),
    password: str = Form(""),
    role: str = Form("admin"),
    is_active: str = Form(""),
):
    user = require_auth(request)
    if not user or user.get("role") != "superadmin":
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.admin.interface import admin_usecase
    admin_usecase.update(
        admin_id=id, name=name, password=password,
        role=role, is_active=is_active == "true",
    )
    return RedirectResponse(url="/admin/admins?msg=Admin+saved", status_code=303)


@router.post("/admins/{id}/delete")
def admins_delete(request: Request, id: str):
    user = require_auth(request)
    if not user or user.get("role") != "superadmin":
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.admin.interface import admin_usecase
    admin_usecase.delete(id)
    return RedirectResponse(url="/admin/admins?msg=Admin+saved", status_code=303)


# ==================== EXPORT ROUTES ====================

@router.get("/export/houses")
def export_houses(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    houses = list(db.houses.find().sort("block", 1))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Block", "House Number", "Street", "Status", "Address Note"])
        for h in houses:
            writer.writerow([h.get("block", ""), h.get("house_number", ""), h.get("street", ""), h.get("status", ""), h.get("address_note", "")])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=houses.csv"})

    # PDF - simple HTML table rendered as PDF-like download
    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>Houses</h2><table><tr><th>Block</th><th>No</th><th>Street</th><th>Status</th></tr>"
    for h in houses:
        html += f"<tr><td>{h.get('block', '')}</td><td>{h.get('house_number', '')}</td><td>{h.get('street', '')}</td><td>{h.get('status', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=houses.html"})


@router.get("/export/vehicles")
def export_vehicles(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    vehicles = list(db.vehicles.find().sort("plate_number", 1))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Plate Number", "Type", "Brand", "Model", "Color", "Year", "Active"])
        for v in vehicles:
            writer.writerow([v.get("plate_number", ""), v.get("type", ""), v.get("brand", ""), v.get("model", ""), v.get("color", ""), v.get("year", ""), v.get("is_active", "")])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=vehicles.csv"})

    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>Vehicles</h2><table><tr><th>Plate</th><th>Type</th><th>Brand</th><th>Model</th><th>Color</th><th>Year</th><th>Active</th></tr>"
    for v in vehicles:
        html += f"<tr><td>{v.get('plate_number', '')}</td><td>{v.get('type', '')}</td><td>{v.get('brand', '')}</td><td>{v.get('model', '')}</td><td>{v.get('color', '')}</td><td>{v.get('year', '')}</td><td>{v.get('is_active', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=vehicles.html"})


@router.get("/export/families")
def export_families(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    families = list(db.families.find().sort("head_name", 1))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Head Name", "Phone", "ID Number", "Members", "Status"])
        for f in families:
            writer.writerow([f.get("head_name", ""), f.get("head_phone", ""), f.get("head_id_number", ""), f.get("total_members", ""), f.get("status", "")])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=families.csv"})

    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>Families</h2><table><tr><th>Head Name</th><th>Phone</th><th>Members</th><th>Status</th></tr>"
    for f in families:
        html += f"<tr><td>{f.get('head_name', '')}</td><td>{f.get('head_phone', '')}</td><td>{f.get('total_members', '')}</td><td>{f.get('status', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=families.html"})


@router.get("/export/guests")
def export_guests(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    guests = list(db.guests.find().sort("entry_time", -1).limit(1000))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Phone", "Purpose", "Vehicle Plate", "Entry Time", "Exit Time", "Status"])
        for g in guests:
            entry = g.get("entry_time", "")
            if hasattr(entry, "strftime"):
                entry = entry.strftime("%Y-%m-%d %H:%M:%S")
            exit_time = g.get("exit_time", "")
            if hasattr(exit_time, "strftime"):
                exit_time = exit_time.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([g.get("guest_name", ""), g.get("guest_phone", ""), g.get("purpose", ""), g.get("vehicle_plate", ""), entry, exit_time, g.get("status", "")])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=guests.csv"})

    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>Guests</h2><table><tr><th>Name</th><th>Phone</th><th>Purpose</th><th>Vehicle</th><th>Entry</th><th>Status</th></tr>"
    for g in guests:
        entry = g.get("entry_time", "")
        if hasattr(entry, "strftime"):
            entry = entry.strftime("%Y-%m-%d %H:%M")
        html += f"<tr><td>{g.get('guest_name', '')}</td><td>{g.get('guest_phone', '')}</td><td>{g.get('purpose', '')}</td><td>{g.get('vehicle_plate', '')}</td><td>{entry}</td><td>{g.get('status', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=guests.html"})


@router.get("/export/access-logs")
def export_access_logs(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    logs = list(db.access_logs.find().sort("timestamp", -1).limit(1000))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Gate", "Direction", "Method", "Plate", "Confidence", "Result", "Reason"])
        for l in logs:
            ts = l.get("timestamp", "")
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                ts, l.get("gate_id", ""), l.get("direction", ""),
                l.get("method", ""), l.get("plate_detected", ""), l.get("plate_confidence", ""),
                l.get("validation_result", ""), l.get("denied_reason", "")
            ])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=access_logs.csv"})

    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>Access Logs</h2><table><tr><th>Time</th><th>Gate</th><th>Dir</th><th>Method</th><th>Plate</th><th>Conf</th><th>Result</th></tr>"
    for l in logs:
        ts = l.get("timestamp", "")
        if hasattr(ts, "strftime"):
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
        html += f"<tr><td>{ts}</td><td>{l.get('gate_id', '')}</td><td>{l.get('direction', '')}</td><td>{l.get('method', '')}</td><td>{l.get('plate_detected', '')}</td><td>{l.get('plate_confidence', '')}</td><td>{l.get('validation_result', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=access_logs.html"})


@router.get("/export/rfid")
def export_rfid(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    cards = list(db.rfid_cards.find().sort("card_uid", 1))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Card UID", "Holder", "Type", "Active", "Last Used"])
        for c in cards:
            last_used = c.get("last_used_at", "")
            if hasattr(last_used, "strftime"):
                last_used = last_used.strftime("%Y-%m-%d %H:%M")
            writer.writerow([c.get("card_uid", ""), c.get("holder_name", ""), c.get("card_type", ""), c.get("is_active", ""), last_used])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=rfid_cards.csv"})

    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>RFID Cards</h2><table><tr><th>UID</th><th>Holder</th><th>Type</th><th>Active</th></tr>"
    for c in cards:
        html += f"<tr><td>{c.get('card_uid', '')}</td><td>{c.get('holder_name', '')}</td><td>{c.get('card_type', '')}</td><td>{c.get('is_active', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=rfid_cards.html"})


@router.get("/export/dues")
def export_dues(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    from usecases.due.interface import due_usecase
    db = get_db()
    dues_raw = list(db.dues.find().sort([("year", -1), ("month", -1)]).limit(1000))
    # Enrich with family + house
    dues_data = []
    for d in dues_raw:
        dues_data.append({"_id": str(d["_id"]), "family_id": str(d.get("familyId", "")), "period": d.get("period", ""), "year": d.get("year"), "month": d.get("month"), "type": d.get("type", ""), "amount": d.get("amount", 0), "paid_amount": d.get("paidAmount", 0), "status": d.get("status", ""), "payment_method": d.get("paymentMethod", "")})
    dues_data = due_usecase.enrich_with_family(dues_data)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Kepala Keluarga (Blok)", "Period", "Type", "Amount", "Paid Amount", "Status", "Payment Method"])
        for d in dues_data:
            period = d.get("period", "")
            if not period and d.get("year") and d.get("month"):
                period = f"{d['year']:04d}-{d['month']:02d}"
            writer.writerow([d.get("family_head_name", ""), period, d.get("type", ""), d.get("amount", ""), d.get("paid_amount", ""), d.get("status", ""), d.get("payment_method", "")])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=dues.csv"})

    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>Dues (Iuran)</h2><table><tr><th>Kepala Keluarga (Blok)</th><th>Period</th><th>Type</th><th>Amount</th><th>Paid</th><th>Status</th></tr>"
    for d in dues_data:
        period = d.get("period", "")
        if not period and d.get("year") and d.get("month"):
            period = f"{d['year']:04d}-{d['month']:02d}"
        html += f"<tr><td>{d.get('family_head_name', '')}</td><td>{period}</td><td>{d.get('type', '')}</td><td>{d.get('amount', '')}</td><td>{d.get('paid_amount', '')}</td><td>{d.get('status', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=dues.html"})


@router.get("/export/events")
def export_events(request: Request, format: str = "csv"):
    user = require_auth(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_db()
    events = list(db.events.find().sort("start_date", -1).limit(1000))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Title", "Type", "Start Date", "Location", "Status"])
        for e in events:
            start = e.get("start_date", "")
            if hasattr(start, "strftime"):
                start = start.strftime("%Y-%m-%d")
            writer.writerow([e.get("title", ""), e.get("type", ""), start, e.get("location", ""), e.get("status", "")])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=events.csv"})

    html = "<html><head><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
    html += "<h2>Events</h2><table><tr><th>Title</th><th>Type</th><th>Date</th><th>Location</th><th>Status</th></tr>"
    for e in events:
        start = e.get("start_date", "")
        if hasattr(start, "strftime"):
            start = start.strftime("%Y-%m-%d")
        html += f"<tr><td>{e.get('title', '')}</td><td>{e.get('type', '')}</td><td>{start}</td><td>{e.get('location', '')}</td><td>{e.get('status', '')}</td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html, headers={"Content-Disposition": "attachment; filename=events.html"})
