"""
Resets (drops & recreates) the database and seeds demo data for all roles.

Run:
  python seed.py

Logins (fixed):
  admin@test.com / 1234       (UserAdmin)
  csr@test.com   / 1234       (CSRRep)
  pin@test.com   / 1234       (PersonInNeed)
  pm@test.com    / 1234       (PlatformManager)

This script also creates:
  +10 extra CSR users  → csr+01@test.com ... csr+10@test.com
  +10 extra PIN users  → pin+01@test.com ... pin+10@test.com
  10 requests per category (Transportation, Medical Aid, Food Support) spread over recent days
  Shortlists & completed MatchRecords for realistic testing (incl. date filters).
"""

from datetime import datetime, timedelta
from app import create_app, db
from app.entity.user_profile import UserProfile
from app.entity.user_account import UserAccount
from app.entity.category import Category
from app.entity.request import Request
from app.entity.shortlist import Shortlist
from app.entity.match_record import MatchRecord
from app.entity.report import Report


def mk_phone(i: int) -> str:
    # Singapore-style 8-digit number; deterministic
    base = 81230000 + i
    return str(base)


def add_user(name: str, email: str, profile: UserProfile, phone_idx: int, age: int = 30, active: bool = True) -> UserAccount:
    u = UserAccount(
        name=name,
        email=email,
        profileID=profile.profileID,
        phoneNumber=mk_phone(phone_idx),
        age=age,
        isActive=active,
    )
    u.password = "1234"
    db.session.add(u)
    return u


def reset_and_seed():
    app = create_app()
    with app.app_context():
        # --- 1) Reset DB ---
        db.drop_all()
        db.create_all()

        # --- 2) Profiles (roles) ---
        p_admin = UserProfile(profileName="UserAdmin", description="Manages users and profiles")
        p_csr   = UserProfile(profileName="CSRRep", description="Corporate Social Responsibility representative")
        p_pin   = UserProfile(profileName="PersonInNeed", description="Person in Need")
        p_pm    = UserProfile(profileName="PlatformManager", description="Manages categories and reports")
        db.session.add_all([p_admin, p_csr, p_pin, p_pm])
        db.session.commit()

        # --- 3) Core demo users (fixed logins) ---
        u_admin = add_user("Admin User", "admin@test.com", p_admin, phone_idx=1, age=35)
        u_csr   = add_user("CSR User",   "csr@test.com",   p_csr,   phone_idx=2, age=32)
        u_pin   = add_user("PIN User",   "pin@test.com",   p_pin,   phone_idx=3, age=66)
        u_pm    = add_user("PM User",    "pm@test.com",    p_pm,    phone_idx=4, age=40)
        db.session.flush()  # get IDs

        # --- 4) Extra users for testing ---
        extra_csrs = []
        for i in range(1, 11):
            idx = 100 + i
            extra_csrs.append(
                add_user(
                    name=f"CSR Rep {i:02d}",
                    email=f"csr+{i:02d}@test.com",
                    profile=p_csr,
                    phone_idx=idx,
                    age=28 + (i % 10),
                )
            )

        extra_pins = []
        for i in range(1, 10 + 1):
            idx = 200 + i
            extra_pins.append(
                add_user(
                    name=f"PIN Person {i:02d}",
                    email=f"pin+{i:02d}@test.com",
                    profile=p_pin,
                    phone_idx=idx,
                    age=55 + (i % 15),
                )
            )

        db.session.commit()

        # --- 5) Categories ---
        c_transport = Category(categoryName="Transportation", description="Transport assistance", isActive=True)
        c_medical   = Category(categoryName="Medical Aid",    description="Medical support",   isActive=True)
        c_food      = Category(categoryName="Food Support",   description="Food & groceries",  isActive=True)
        db.session.add_all([c_transport, c_medical, c_food])
        db.session.commit()

        # --- 6) Requests (10 per category), spread over last 14 days ---
        now = datetime.utcnow()

        def new_request(pin: UserAccount, cat: Category, idx: int) -> Request:
            title_map = {
                c_transport.categoryID: "Transport to appointment",
                c_medical.categoryID:   "Medical supply support",
                c_food.categoryID:      "Groceries delivery assistance",
            }
            desc_map = {
                c_transport.categoryID: "Wheelchair-friendly transport needed",
                c_medical.categoryID:   "Request for basic medical items",
                c_food.categoryID:      "Weekly groceries delivery preferred",
            }
            created = now - timedelta(days=idx % 12 + 1)
            r = Request(
                pinID=pin.userID,
                categoryID=cat.categoryID,
                title=title_map[cat.categoryID],
                description=desc_map[cat.categoryID],
                status="open",                 # may flip to closed below
                viewCount= (idx % 5) + 1,
                shortlistCount=0,              # updated if shortlisted
                createdAt=created,
                closedAt=None,
            )
            db.session.add(r)
            return r

        all_requests = []

        # assign requests across multiple PINs to be realistic
        def pin_for(i: int) -> UserAccount:
            # rotate among fixed u_pin and extras
            if i % 11 == 0:
                return u_pin
            return extra_pins[(i - 1) % len(extra_pins)]

        categories = [c_transport, c_medical, c_food]

        req_index = 0
        for cat in categories:
            for i in range(1, 10 + 1):  # 10 per category
                req_index += 1
                r = new_request(pin_for(req_index), cat, idx=req_index)
                all_requests.append(r)

        db.session.flush()  # requestIDs available

        # --- 7) Shortlists & Matches ---
        # Rule of thumb:
        # - Every 2nd request gets shortlisted by the fixed u_csr
        # - Every 3rd request is completed (closed) with a MatchRecord by a rotating CSR
        # - Completion dates include edge cases (e.g., same-day periods)
        rotating_csrs = [u_csr] + extra_csrs

        match_records = []
        for i, r in enumerate(all_requests, start=1):
            # shortlist some
            if i % 2 == 0:
                s = Shortlist(csrRepID=rotating_csrs[i % len(rotating_csrs)].userID, requestID=r.requestID)
                db.session.add(s)
                r.shortlistCount = (r.shortlistCount or 0) + 1

            # complete every 3rd request
            if i % 3 == 0:
                r.status = "closed"
                closed = r.createdAt + timedelta(days=1 + (i % 4))
                r.closedAt = closed

                mr = MatchRecord(
                    requestID=r.requestID,
                    csrRepID=rotating_csrs[i % len(rotating_csrs)].userID,
                    pinID=r.pinID,
                    categoryID=r.categoryID,
                    status="completed",
                    matchedAt=r.createdAt + timedelta(hours=6),
                    completedAt=closed.replace(hour=(8 + i) % 20, minute=(5 * i) % 60, second=0),
                )
                match_records.append(mr)

        db.session.add_all(match_records)
        db.session.commit()

        # --- 8) Keep your original two demo requests (for reference) ---
        r1 = Request(
            pinID=u_pin.userID,
            categoryID=c_transport.categoryID,
            title="Wheelchair-friendly transport needed",
            description="Pickup to hospital appointment",
            status="closed",
            viewCount=3,
            shortlistCount=1,
            createdAt=now - timedelta(days=5),
            closedAt=now - timedelta(days=3),
        )
        r2 = Request(
            pinID=u_pin.userID,
            categoryID=c_food.categoryID,
            title="Groceries delivery assistance",
            description="Weekly delivery preferred",
            status="open",
            viewCount=1,
            shortlistCount=0,
            createdAt=now - timedelta(days=2),
        )
        db.session.add_all([r1, r2])
        db.session.flush()

        # shortlist + match for r1
        s1 = Shortlist(csrRepID=u_csr.userID, requestID=r1.requestID)
        m1 = MatchRecord(
            requestID=r1.requestID,
            csrRepID=u_csr.userID,
            pinID=u_pin.userID,
            categoryID=c_transport.categoryID,
            status="completed",
            matchedAt=now - timedelta(days=4, hours=2),
            completedAt=now - timedelta(days=3, hours=1),
        )
        db.session.add_all([s1, m1])
        db.session.commit()

        # --- 9) Reports (Platform Manager) ---
        rep_daily = Report(
            reportTitle="Daily System Report - Demo",
            reportType="daily",
            generatedBy=u_pm.userID,
            period=(now - timedelta(days=1)).strftime("%Y-%m-%d"),
            reportData='{"summary": {"note":"daily demo data"}}'
        )
        rep_weekly = Report(
            reportTitle="Weekly System Report - Demo",
            reportType="weekly",
            generatedBy=u_pm.userID,
            period=(now - timedelta(days=7)).strftime("%Y-W%U"),
            reportData='{"summary": {"note":"weekly demo data"}}'
        )
        rep_monthly = Report(
            reportTitle="Monthly System Report - Demo",
            reportType="monthly",
            generatedBy=u_pm.userID,
            period=now.strftime("%Y-%m"),
            reportData='{"summary": {"note":"monthly demo data"}}'
        )
        db.session.add_all([rep_daily, rep_weekly, rep_monthly])
        db.session.commit()

        print("✅ Database reset complete.")
        print("👤 Demo users:")
        print("  - admin@test.com / 1234 (UserAdmin)")
        print("  - csr@test.com   / 1234 (CSRRep)")
        print("  - pin@test.com   / 1234 (PersonInNeed)")
        print("  - pm@test.com    / 1234 (PlatformManager)")
        print("👥 Extra users:")
        print("  - 10 CSR users   (csr+01@test.com .. csr+10@test.com)")
        print("  - 10 PIN users   (pin+01@test.com .. pin+10@test.com)")
        print("🗂️  Categories: Transportation, Medical Aid, Food Support")
        print(f"📝 Requests created: {len(all_requests) + 2} (10 per category + 2 originals)")
        print(f"✅ MatchRecords created: {len(match_records) + 1} (includes original r1)")
        print("ℹ️ Try filtering by category and date ranges, including same-day searches.")


if __name__ == "__main__":
    reset_and_seed()
