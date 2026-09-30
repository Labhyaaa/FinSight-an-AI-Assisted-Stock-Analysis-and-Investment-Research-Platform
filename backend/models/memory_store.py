# pyre-ignore-all-errors
"""
FinSight - In-Memory Data Store
Provides a complete in-memory database for running without PostgreSQL.
Pre-populated with the same seed data as seed_data.sql.
"""
import random
import math
from datetime import datetime, timedelta, timezone
from copy import deepcopy

# ── Helper: generate realistic price history ─────────────────
def _gen_price_history(base_price, days=365, volatility=0.02):
    """Generate mock OHLCV data for the given number of days."""
    data = []
    price = base_price * 0.85  # start lower, trend up
    now = datetime.now(timezone.utc)
    for i in range(days, 0, -1):
        change = random.gauss(0.0003, volatility)
        price *= (1 + change)
        o = round(price * random.uniform(0.995, 1.005), 2)
        h = round(price * random.uniform(1.005, 1.025), 2)
        l = round(price * random.uniform(0.975, 0.995), 2)
        c = round(price, 2)
        vol = random.randint(500000, 5000000)
        ts = (now - timedelta(days=i)).strftime("%Y-%m-%dT09:15:00Z")
        data.append({"timestamp": ts, "open": o, "high": h, "low": l, "close": c, "volume": vol})
    return data


# ══════════════════════════════════════════════════════════════
#  SEED DATA
# ══════════════════════════════════════════════════════════════

# ── Users ────────────────────────────────────────────────────
_USERS = [
    {
        "id": 1, "email": "admin@finsight.ai", "name": "Admin",
        # bcrypt hash for "Password@123" - in memory mode we check plaintext
        "password_hash": "Password@123",
        "role": "admin", "is_active": True, "is_email_verified": True,
        "age": 30, "country": "India", "risk_profile": "Aggressive",
        "experience_level": "Professional",
        "monthly_investment_capacity": 50000, "yearly_investment_capacity": 600000,
        "goals": "Platform management",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": None,
    },
    {
        "id": 2, "email": "rahul@example.com", "name": "Rahul Sharma",
        "password_hash": "Password@123",
        "role": "user", "is_active": True, "is_email_verified": True,
        "age": 28, "country": "India", "risk_profile": "Moderate",
        "experience_level": "Beginner",
        "monthly_investment_capacity": 10000, "yearly_investment_capacity": 120000,
        "goals": "Wealth creation, Retirement",
        "created_at": "2026-01-15T00:00:00Z", "updated_at": None,
    },
    {
        "id": 3, "email": "priya@example.com", "name": "Priya Patel",
        "password_hash": "Password@123",
        "role": "user", "is_active": True, "is_email_verified": True,
        "age": 32, "country": "India", "risk_profile": "Conservative",
        "experience_level": "Intermediate",
        "monthly_investment_capacity": 25000, "yearly_investment_capacity": 300000,
        "goals": "Tax saving, Education fund",
        "created_at": "2026-02-01T00:00:00Z", "updated_at": None,
    },
    {
        "id": 4, "email": "lagangupta042006@gmail.com", "name": "lagan gupta",
        "password_hash": "ownerpassword",
        "role": "user", "is_active": True, "is_email_verified": True,
        "age": 20, "country": "India", "risk_profile": "Moderate",
        "experience_level": "Beginner",
        "monthly_investment_capacity": 20000, "yearly_investment_capacity": 240000,
        "goals": "",
        "created_at": "2026-03-23T00:00:00Z", "updated_at": None,
        "dob": "4 march 2006", "mobile_number": "8619202830",
        "marital_status": "single", "gender": "male",
        "income_range": "1000000", "occupation": "student",
        "fathers_name": "sunil kumar gupta"
    },
    {
        "id": 5, "email": "b241236@skit.ac.in", "name": "Labhya Sharma",
        "password_hash": "labhya123",
        "role": "user", "is_active": True, "is_email_verified": True,
        "age": 20, "country": "India", "risk_profile": "Moderate",
        "experience_level": "Beginner",
        "monthly_investment_capacity": 10000, "yearly_investment_capacity": 120000,
        "goals": "Wealth creation",
        "created_at": "2026-09-14T00:00:00Z", "updated_at": None,
    },
]

# ── Instruments (imported from generated data) ───────────────
import sys as _sys, os as _os
_project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_scripts_dir = _os.path.join(_project_root, "scripts")
if _scripts_dir not in _sys.path:
    _sys.path.insert(0, _scripts_dir)
from generated_data import GENERATED_INSTRUMENTS, GENERATED_FUND_DATA
_INSTRUMENTS = GENERATED_INSTRUMENTS

# ── Fundamentals ─────────────────────────────────────────────
def _make_fundamentals(inst_id, pe, pb, roe, roce, eps, de, npm, ph, sg, pg, rev, np_val):
    """Generate 3 years of fundamentals for one instrument."""
    def _r(val, factor=1.0, ndigits=2):
        return round(val * factor, ndigits) if val is not None else None

    rows = []
    for yr_offset, year in enumerate(["FY2026", "FY2025", "FY2024"]):
        factor = 1.0 - yr_offset * 0.08  # slight decrease going back
        rows.append({
            "id": inst_id * 10 + yr_offset, "instrument_id": inst_id,
            "fiscal_year": year,
            "revenue": round(rev * factor, 2), "net_profit": round(np_val * factor, 2),
            "eps": round(eps * factor, 2),
            "debt": round(de * rev * 0.1, 2) if de is not None else None,
            "equity": round(rev * 0.3, 2),
            "pe": round(pe * (1 + yr_offset * 0.05), 2),
            "pb": round(pb * (1 + yr_offset * 0.03), 2),
            "roe": _r(roe, factor), "roce": _r(roce, factor),
            "debt_to_equity": _r(de),
            "promoter_holding": _r(ph),
            "net_profit_margin": _r(npm, factor),
            "sales_growth": _r(sg, factor),
            "profit_growth": _r(pg, factor),
        })
    return rows

_FUNDAMENTALS = []
_fund_data = GENERATED_FUND_DATA
for fd in _fund_data:
    _FUNDAMENTALS.extend(_make_fundamentals(*fd))

# ── Screeners ────────────────────────────────────────────────
_SCREENERS = [
    {"id":1, "user_id":None, "name":"High ROE Blue Chips", "description":"Companies with ROE > 20% and market cap > 100000 Cr", "definition_json":{"conditions":[{"field":"roe","op":">","value":20},{"field":"market_cap","op":">","value":100000}],"logic":"AND"}},
    {"id":2, "user_id":None, "name":"Low Debt Growth Stocks", "description":"Low leverage companies with strong profit growth", "definition_json":{"conditions":[{"field":"debt_to_equity","op":"<","value":0.3},{"field":"profit_growth","op":">","value":10}],"logic":"AND"}},
    {"id":3, "user_id":None, "name":"Value Picks", "description":"Undervalued stocks with PE < 15 and ROE > 15%", "definition_json":{"conditions":[{"field":"pe","op":"<","value":15},{"field":"roe","op":">","value":15}],"logic":"AND"}},
    {"id":4, "user_id":None, "name":"High Margin Leaders", "description":"Companies with net profit margin > 20%", "definition_json":{"conditions":[{"field":"net_profit_margin","op":">","value":20}],"logic":"AND"}},
    {"id":5, "user_id":None, "name":"Growth Champions", "description":"High sales and profit growth stocks", "definition_json":{"conditions":[{"field":"sales_growth","op":">","value":12},{"field":"profit_growth","op":">","value":15}],"logic":"AND"}},
    {"id":6, "user_id":None, "name":"Large Cap Compounders", "description":"Large caps with consistent growth and high ROE", "definition_json":{"conditions":[{"field":"market_cap","op":">","value":50000},{"field":"roe","op":">","value":15},{"field":"sales_growth","op":">","value":10}],"logic":"AND"}},
    {"id":7, "user_id":None, "name":"Debt-Free Compounders", "description":"Companies with almost no debt and high ROCE", "definition_json":{"conditions":[{"field":"debt_to_equity","op":"<","value":0.1},{"field":"roce","op":">","value":20}],"logic":"AND"}},
    {"id":8, "user_id":None, "name":"Deep Value", "description":"Extremely cheap stocks based on earnings and book value", "definition_json":{"conditions":[{"field":"pe","op":"<","value":15},{"field":"pb","op":"<","value":2.5}],"logic":"AND"}},
    {"id":9, "user_id":None, "name":"Midcap Growth Stars", "description":"Mid-sized companies showing strong profit growth", "definition_json":{"conditions":[{"field":"market_cap","op":">","value":5000},{"field":"profit_growth","op":">","value":20}],"logic":"AND"}},
    {"id":10, "user_id":None, "name":"Efficient Capital Allocators", "description":"Companies generating high returns on capital", "definition_json":{"conditions":[{"field":"roce","op":">","value":25},{"field":"roe","op":">","value":20}],"logic":"AND"}},
    {"id":11, "user_id":None, "name":"Rapid Profit Growers", "description":"Companies growing profits at an exceptional rate", "definition_json":{"conditions":[{"field":"profit_growth","op":">","value":30},{"field":"sales_growth","op":">","value":20}],"logic":"AND"}},
    {"id":12, "user_id":None, "name":"Microcap Gems", "description":"Small companies with explosive growth metrics", "definition_json":{"conditions":[{"field":"market_cap","op":"<","value":15000},{"field":"profit_growth","op":">","value":15},{"field":"roe","op":">","value":15}],"logic":"AND"}}
]

# ── Watchlists (start with one for demo) ─────────────────────
_WATCHLISTS = [
    {"id":1, "user_id":2, "name":"My Watchlist", "created_at":"2026-02-01T00:00:00Z"},
    {"id":2, "user_id":4, "name":"Tech & Growth", "created_at":"2026-03-24T00:00:00Z"},
    {"id":3, "user_id":4, "name":"Core Portfolio", "created_at":"2026-03-24T00:00:00Z"},
]
_WATCHLIST_ITEMS = [
    {"id":1, "watchlist_id":1, "instrument_id":1, "added_at":"2026-02-01T00:00:00Z"},
    {"id":2, "watchlist_id":1, "instrument_id":5, "added_at":"2026-02-02T00:00:00Z"},
    {"id":3, "watchlist_id":1, "instrument_id":12, "added_at":"2026-02-03T00:00:00Z"},
    # Tech & Growth watchlist
    {"id":4, "watchlist_id":2, "instrument_id":18, "added_at":"2026-03-24T00:00:00Z"}, # TCS
    {"id":5, "watchlist_id":2, "instrument_id":19, "added_at":"2026-03-24T00:00:00Z"}, # INFY
    {"id":6, "watchlist_id":2, "instrument_id":492, "added_at":"2026-03-24T00:00:00Z"}, # NIFTY 50
    # Core Portfolio watchlist
    {"id":7, "watchlist_id":3, "instrument_id":1, "added_at":"2026-03-24T00:00:00Z"},  # RELIANCE
    {"id":8, "watchlist_id":3, "instrument_id":4, "added_at":"2026-03-24T00:00:00Z"},  # HDFCBANK
]

# ── Portfolio Positions ──────────────────────────────────────
_POSITIONS = [
    {"id":1, "user_id":2, "instrument_id":1, "quantity":10, "buy_price":3500.00, "buy_date":"2025-12-15"},
    {"id":2, "user_id":2, "instrument_id":5, "quantity":25, "buy_price":1600.00, "buy_date":"2025-11-20"},
    {"id":3, "user_id":2, "instrument_id":12, "quantity":15, "buy_price":2480.00, "buy_date":"2025-10-10"},
    # Positions for user 4 (Lagan Gupta)
    {"id":4, "user_id":4, "instrument_id":1, "quantity":50, "buy_price":2800.00, "buy_date":"2025-06-15"}, # RELIANCE
    {"id":5, "user_id":4, "instrument_id":4, "quantity":150, "buy_price":1450.00, "buy_date":"2025-08-20"}, # HDFCBANK
    {"id":6, "user_id":4, "instrument_id":18, "quantity":30, "buy_price":3800.00, "buy_date":"2025-10-10"}, # TCS
    {"id":7, "user_id":4, "instrument_id":51, "quantity":10, "buy_price":6100.00, "buy_date":"2026-01-05"}, # BAJFINANCE
    {"id":8, "user_id":4, "instrument_id":492, "quantity":5, "buy_price":21000.00, "buy_date":"2025-12-01"}, # NIFTY 50 (Index Fund proxy)
]

# ── OTPs ─────────────────────────────────────────────────────
_OTPS = []

# ── Chat Logs ────────────────────────────────────────────────
_CHAT_LOGS = []

# ── Settings ─────────────────────────────────────────────────
_SETTINGS = [
    {"id":1, "key":"market_open_time", "value":"09:15"},
    {"id":2, "key":"market_close_time", "value":"15:30"},
    {"id":3, "key":"default_chart_range", "value":"1M"},
]

# ── Price History Cache (lazy-generated) ─────────────────────
_PRICE_CACHE = {}

# Auto-increment counters
_COUNTERS = {
    "users": 5,
    "otps": 1,
    "watchlists": 4,
    "watchlist_items": 9,
    "positions": 9,
    "screeners": 13,
    "chat_logs": 1,
}

def _next_id(table):
    _COUNTERS[table] = _COUNTERS.get(table, 1) + 1
    return _COUNTERS[table] - 1


# ══════════════════════════════════════════════════════════════
#  PUBLIC API  –  mirrors the model functions
# ══════════════════════════════════════════════════════════════

# ── User functions ───────────────────────────────────────────
def user_create(email, password_hash, name):
    uid = _next_id("users")
    user = {
        "id": uid, "email": email, "password_hash": password_hash, "name": name,
        "role": "user", "is_active": True, "is_email_verified": False,
        "age": None, "country": "India", "risk_profile": "Moderate",
        "experience_level": "Beginner",
        "monthly_investment_capacity": None, "yearly_investment_capacity": None,
        "goals": None, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": None,
    }
    _USERS.append(user)
    return {"id": uid, "email": email, "name": name, "role": "user"}


def user_find_by_email(email):
    for u in _USERS:
        email_val = u.get("email")
        if email_val and str(email_val).lower() == email.lower():
            return deepcopy(u)
    return None


def user_find_by_id(user_id):
    for u in _USERS:
        if u["id"] == user_id:
            return deepcopy(u)
    return None


def user_update_profile(user_id, data):
    allowed = ["name","age","country","risk_profile","experience_level",
               "monthly_investment_capacity","yearly_investment_capacity","goals",
               "dob", "mobile_number", "marital_status", "gender", "income_range", "occupation", "fathers_name"]
    for u in _USERS:
        if u["id"] == user_id:
            for k, v in data.items():
                if k in allowed:
                    u[k] = v
            u["updated_at"] = datetime.now(timezone.utc).isoformat()
            return


def user_verify_email(user_id):
    for u in _USERS:
        if u["id"] == user_id:
            u["is_email_verified"] = True
            return


def user_list_all():
    return [
        {k: u[k] for k in ("id","email","name","role","is_active","is_email_verified","created_at")}
        for u in _USERS
    ]


def user_toggle_active(user_id):
    for u in _USERS:
        if u["id"] == user_id:
            u["is_active"] = not u["is_active"]
            return {"is_active": u["is_active"]}
    return None

def instrument_get_by_type(inst_type, sector=None, sort_by=None, page=1, limit=50):
    results = [i for i in _INSTRUMENTS if i.get("type") == inst_type.lower() and i.get("is_active")]
    if sector:
        results = [i for i in results if (i.get("sector") or "").lower() == sector.lower() or (i.get("industry") or "").lower() == sector.lower()]
        
    if sort_by == 'price_desc':
        results.sort(key=lambda x: x.get("current_price") or 0, reverse=True)
    elif sort_by == 'price_asc':
        results.sort(key=lambda x: x.get("current_price") or 0, reverse=False)
    elif sort_by == 'change_desc':
        results.sort(key=lambda x: x.get("day_change_pct") or -999, reverse=True)
    elif sort_by == 'change_asc':
        results.sort(key=lambda x: x.get("day_change_pct") or 999, reverse=False)
    elif sort_by == 'name_asc':
        results.sort(key=lambda x: x.get("name") or "", reverse=False)
    elif sort_by == 'name_desc':
        results.sort(key=lambda x: x.get("name") or "", reverse=True)
    else: # Default market_cap desc
        results.sort(key=lambda x: x.get("market_cap") or 0, reverse=True)
        
    total = len(results)
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "items": [deepcopy(r) for r in results[start:end]],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


def user_find_by_phone(phone):
    """Look up a user by their mobile_number field."""
    phone_clean = str(phone).strip().replace("+91", "").replace(" ", "").replace("-", "")
    for u in _USERS:
        val = u.get("mobile_number")
        stored = str(val).strip().replace("+91", "").replace(" ", "").replace("-", "") if val else ""
        if stored and stored == phone_clean:
            return deepcopy(u)
    return None


def user_update_password(user_id, password_hash):
    """Update a user's password hash."""
    for u in _USERS:
        if u["id"] == user_id:
            u["password_hash"] = password_hash
            u["updated_at"] = datetime.now(timezone.utc).isoformat()
            return True
    return False


# ── OTP functions ────────────────────────────────────────────
def otp_create(user_id, otp_code, expiry_minutes=10):
    _OTPS.append({
        "id": _next_id("otps"), "user_id": user_id, "otp_code": otp_code,
        "is_used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def otp_verify(user_id, otp_code):
    now = datetime.now(timezone.utc).isoformat()
    for otp in reversed(_OTPS):
        if (otp["user_id"] == user_id and otp["otp_code"] == otp_code
                and not otp["is_used"] and otp["expires_at"] > now):
            otp["is_used"] = True
            return True
    return False


# ── Instrument functions ─────────────────────────────────────
def instrument_search(query, limit=20):
    q = query.lower()
    results = [i for i in _INSTRUMENTS if q in i["name"].lower() or q in i["symbol"].lower()]
    results.sort(key=lambda x: x.get("market_cap") or 0, reverse=True)
    return [deepcopy(r) for r in results[:limit]]


def instrument_get_all():
    return [deepcopy(i) for i in _INSTRUMENTS if i.get("is_active")]


def instrument_get(instrument_id):
    for i in _INSTRUMENTS:
        if i["id"] == instrument_id:
            return deepcopy(i)
    return None


def instrument_get_fundamentals(instrument_id):
    rows = [f for f in _FUNDAMENTALS if f["instrument_id"] == instrument_id]
    rows.sort(key=lambda x: x["fiscal_year"], reverse=True)
    return [deepcopy(r) for r in rows]


def instrument_get_by_sector(sector):
    results = [i for i in _INSTRUMENTS if (i.get("sector") or "").lower() == sector.lower()]
    results.sort(key=lambda x: x.get("market_cap") or 0, reverse=True)
    return [deepcopy(r) for r in results]


def instrument_get_sectors():
    sectors = {}
    for i in _INSTRUMENTS:
        s = i.get("sector")
        if not s:
            continue
        if s not in sectors:
            sectors[s] = {"sector": s, "instrument_count": 0, "pct_sum": 0}
        sectors[s]["instrument_count"] += 1
        sectors[s]["pct_sum"] += (i.get("day_change_pct") or 0)
    result = []
    for s in sorted(sectors.values(), key=lambda x: x["sector"]):
        avg = round(s["pct_sum"] / s["instrument_count"], 2) if s["instrument_count"] else 0
        result.append({"sector": s["sector"], "instrument_count": s["instrument_count"], "avg_day_change_pct": avg})
    return result


def instrument_get_chart(instrument_id, range_str="1M"):
    if instrument_id not in _PRICE_CACHE:
        inst = instrument_get(instrument_id)
        if not inst:
            return []
        _PRICE_CACHE[instrument_id] = _gen_price_history(inst["current_price"], days=365*3)

    data = _PRICE_CACHE[instrument_id]
    range_map = {"1D":1, "1W":7, "1M":30, "3M":90, "6M":180, "1Y":365, "5Y":365*3, "MAX":365*3}
    days = range_map.get(range_str, 30)
    return data[-days:]


# ── FinSight functions ───────────────────────────────────────
def finsight_get_predefined():
    return [deepcopy(s) for s in _SCREENERS if s["user_id"] is None]


def finsight_get_user(user_id):
    return [deepcopy(s) for s in _SCREENERS if s["user_id"] == user_id]


def finsight_create(user_id, name, description, definition_json):
    sid = _next_id("screeners")
    s = {"id": sid, "user_id": user_id, "name": name, "description": description,
         "definition_json": definition_json}
    _SCREENERS.append(s)
    return {"id": sid, "name": name}


def finsight_run(definition_json):
    import json as _json
    defn = _json.loads(definition_json) if isinstance(definition_json, str) else definition_json
    conditions = defn.get("conditions", [])
    logic = defn.get("logic", "AND").upper()

    results = []
    for inst in _INSTRUMENTS:
        # Get latest fundamentals
        funds = [f for f in _FUNDAMENTALS if f["instrument_id"] == inst["id"]]
        if not funds:
            continue
        funds.sort(key=lambda x: x["fiscal_year"], reverse=True)
        latest = funds[0]

        matches = []
        for cond in conditions:
            field = cond.get("field", "")
            op = cond.get("op", "")
            val = cond.get("value")
            if val is None:
                continue

            if field == "market_cap":
                actual = inst.get("market_cap")
            else:
                actual = latest.get(field)

            if actual is None:
                matches.append(False)
                continue

            if op == ">":   matches.append(actual > val)
            elif op == "<": matches.append(actual < val)
            elif op == ">=": matches.append(actual >= val)
            elif op == "<=": matches.append(actual <= val)
            elif op == "=": matches.append(actual == val)
            elif op == "!=": matches.append(actual != val)
            else: matches.append(False)

        if not matches:
            continue
        passed = all(matches) if logic == "AND" else any(matches)
        if passed:
            row = {**inst, **{k: latest.get(k) for k in (
                "pe","pb","roe","roce","debt_to_equity","net_profit_margin","sales_growth","profit_growth"
            )}}
            results.append(row)

    results.sort(key=lambda x: x.get("market_cap") or 0, reverse=True)
    return results[:50]


# ── Watchlist functions ──────────────────────────────────────
def watchlist_get_all(user_id):
    wls = [deepcopy(w) for w in _WATCHLISTS if w["user_id"] == user_id]
    for wl in wls:
        items = [wi for wi in _WATCHLIST_ITEMS if wi["watchlist_id"] == wl["id"]]
        wl["items"] = []
        for wi in items:
            inst = instrument_get(wi["instrument_id"])
            if inst:
                wl["items"].append({
                    "item_id": wi["id"], "instrument_id": inst["id"],
                    "symbol": inst["symbol"], "name": inst["name"],
                    "current_price": inst["current_price"],
                    "day_change": inst["day_change"],
                    "day_change_pct": inst["day_change_pct"],
                })
    return wls


def watchlist_create(user_id, name):
    wid = _next_id("watchlists")
    wl = {"id": wid, "user_id": user_id, "name": name,
          "created_at": datetime.now(timezone.utc).isoformat()}
    _WATCHLISTS.append(wl)
    return {"id": wid, "name": name}


def watchlist_add_item(watchlist_id, instrument_id):
    # Check duplicate
    for wi in _WATCHLIST_ITEMS:
        if wi["watchlist_id"] == watchlist_id and wi["instrument_id"] == instrument_id:
            return {"message": "Already in watchlist"}
    iid = _next_id("watchlist_items")
    _WATCHLIST_ITEMS.append({
        "id": iid, "watchlist_id": watchlist_id, "instrument_id": instrument_id,
        "added_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"id": iid}


def watchlist_remove_item(watchlist_id, item_id):
    global _WATCHLIST_ITEMS
    _WATCHLIST_ITEMS = [wi for wi in _WATCHLIST_ITEMS
                        if not (wi["watchlist_id"] == watchlist_id and wi["id"] == item_id)]


# ── Portfolio functions ──────────────────────────────────────
def portfolio_get_positions(user_id):
    result = []
    for p in _POSITIONS:
        if p["user_id"] != user_id:
            continue
        inst = instrument_get(p["instrument_id"])
        if not inst:
            continue
        # Guard against None/invalid values
        quantity = p.get("quantity") or 0
        buy_price = p.get("buy_price") or 0
        current_price = inst.get("current_price") or 0
        try:
            quantity = float(quantity)
            buy_price = float(buy_price)
            current_price = float(current_price)
        except (TypeError, ValueError):
            continue
        if quantity <= 0:
            continue
        unrealized_pl = round((current_price - buy_price) * quantity, 2)
        return_pct = round(((current_price - buy_price) / buy_price) * 100, 2) if buy_price > 0 else 0
        result.append({
            "id": p["id"], "quantity": quantity, "buy_price": buy_price,
            "buy_date": p["buy_date"], "instrument_id": inst["id"],
            "symbol": inst["symbol"], "name": inst["name"],
            "current_price": current_price,
            "unrealized_pl": unrealized_pl, "return_pct": return_pct,
        })
    return result


def portfolio_add_position(user_id, instrument_id, quantity, buy_price, buy_date):
    pid = _next_id("positions")
    _POSITIONS.append({
        "id": pid, "user_id": user_id, "instrument_id": int(instrument_id),
        "quantity": float(quantity), "buy_price": float(buy_price),
        "buy_date": buy_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    })
    return {"id": pid, "message": "Position added"}


# ── Chat functions ───────────────────────────────────────────
def chat_log(user_id, instrument_id, user_message, ai_response_summary):
    cid = _next_id("chat_logs")
    entry = {
        "id": cid, "user_id": user_id, "instrument_id": instrument_id,
        "user_message": user_message, "ai_response_summary": ai_response_summary,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _CHAT_LOGS.append(entry)
    return {"id": cid, "created_at": entry["created_at"]}


def chat_get_history(user_id, instrument_id=None, limit=50):
    logs = [cl for cl in _CHAT_LOGS if cl["user_id"] == user_id]
    if instrument_id:
        logs = [cl for cl in logs if cl["instrument_id"] == instrument_id]
    logs.sort(key=lambda x: x["created_at"], reverse=True)
    return logs[:limit]
