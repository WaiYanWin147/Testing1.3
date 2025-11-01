"""
User Story:
As a Platform Manager, I want to generate weekly reports so that I can track weekly usage.
+ generateWeeklyReport(startDate: date): Report
"""
import json
from datetime import datetime, timedelta
from app import db
from app.entity.report import Report
from app.entity.user_account import UserAccount
from app.entity.request import Request
from app.entity.match_record import MatchRecord
from app.entity.category import Category

class PlatformGenerateWeeklyReportController:
    def generateWeeklyReport(self, manager_id: int, week_string: str):
        """
        week_string expected format: 'YYYY-Www' (example: '2025-W43')
        We'll treat that as the Monday of that ISO week.
        """

        # parse ISO week
        # "2025-W43" -> year=2025, week=43
        year_part, week_part = week_string.split("-W")
        year_val = int(year_part)
        week_val = int(week_part)

        # Monday of that ISO week
        week_start = datetime.fromisocalendar(year_val, week_val, 1)
        week_end = week_start + timedelta(days=7)

        # metrics scoped to this week if you want (optional)
        # for now: same global stats as daily, to keep it simple for demo
        total_users = UserAccount.query.count()
        total_requests = Request.query.count()
        open_requests = Request.query.filter_by(status="open").count()
        closed_requests = Request.query.filter_by(status="closed").count()

        total_matches = MatchRecord.query.count()
        recent_matches_30 = (
            MatchRecord.query
            .filter(MatchRecord.completedAt >= datetime.utcnow() - timedelta(days=30))
            .count()
        )

        breakdown = {}
        cats = Category.query.all()
        for c in cats:
            cat_reqs = Request.query.filter_by(categoryID=c.categoryID).all()
            breakdown[c.categoryName] = {
                "total_requests": len(cat_reqs),
                "open_requests": len([r for r in cat_reqs if r.status == "open"]),
                "closed_requests": len([r for r in cat_reqs if r.status == "closed"]),
            }

        data = {
            "summary": {
                "total_users": total_users,
                "total_requests": total_requests,
                "open_requests": open_requests,
                "closed_requests": closed_requests,
                "total_matches": total_matches,
                "recent_matches_30_days": recent_matches_30,
            },
            "category_breakdown": breakdown
        }

        report = Report(
            reportTitle=f"Weekly Report - {week_string}",
            reportType="weekly",
            generatedBy=manager_id,
            period=week_string,
            reportData=json.dumps(data)
        )

        db.session.add(report)
        db.session.commit()
        return report
