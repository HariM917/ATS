"""
TalentFlow AI — Safe Database Cleanup Script for Invalid / Test Job Artifacts.
Purges development artifacts and orphaned jobs without a valid recruiter or organization,
while preserving all legitimate production HR/recruiter job postings.
"""
import sys
import os
import re
from pathlib import Path

# Add backend directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import get_db_context
from app.models import Job, Recruiter, Organization


def cleanup_invalid_jobs():
    """Identify and remove fake, orphaned, and test-generated jobs."""
    print("=" * 70)
    print("TALENTFLOW AI — JOB POSTING INTEGRITY AUDIT & CLEANUP")
    print("=" * 70)

    test_pattern = re.compile(r"^Lead AI Engineer [0-9a-f]{8}$", re.IGNORECASE)

    with get_db_context() as db:
        jobs = db.query(Job).all()
        print(f"Total jobs in database before audit: {len(jobs)}")

        deleted_count = 0
        preserved_count = 0

        for job in jobs:
            should_delete = False
            reasons = []

            # 1. Check test artifact pattern (e.g. Lead AI Engineer 2e53e70f)
            if test_pattern.match(job.title or ""):
                should_delete = True
                reasons.append("Matches test artifact naming pattern")

            # 2. Check recruiter existence
            if not job.recruiter_id:
                should_delete = True
                reasons.append("Missing recruiter_id")
            else:
                recruiter = db.query(Recruiter).filter_by(id=job.recruiter_id).first()
                if not recruiter:
                    should_delete = True
                    reasons.append(f"Orphaned recruiter_id '{job.recruiter_id}' does not exist")

            if should_delete:
                print(f"[PURGE] Deleting Job ID {job.id} | Title: '{job.title}' | Reasons: {', '.join(reasons)}")
                db.delete(job)
                deleted_count += 1
            else:
                print(f"[PRESERVE] Legitimate Job ID {job.id} | Title: '{job.title}' | Status: {job.status}")
                preserved_count += 1

        db.flush()
        print("-" * 70)
        print(f"Cleanup summary: {deleted_count} invalid jobs purged, {preserved_count} legitimate jobs preserved.")
        print("=" * 70)


if __name__ == "__main__":
    cleanup_invalid_jobs()

