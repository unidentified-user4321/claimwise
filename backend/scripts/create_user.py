"""Map an existing Clerk user to an employee: python scripts/create_user.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clerk_backend_api import Clerk
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import CLERK_SECRET_KEY
from app.db.database import SessionLocal
from app.db.models import User


def main() -> None:
    clerk_user_id = input("Existing Clerk user ID (user_...): ").strip()
    if not clerk_user_id.startswith("user_") or len(clerk_user_id) > 255:
        raise SystemExit("Enter a valid Clerk user ID")
    if not CLERK_SECRET_KEY:
        raise SystemExit("Configure CLERK_SECRET_KEY in the root .env first")
    try:
        with Clerk(bearer_auth=CLERK_SECRET_KEY) as clerk:
            clerk.users.get(user_id=clerk_user_id)
    except Exception:
        raise SystemExit("Could not verify this Clerk user. Check the ID, configuration, and connection.") from None
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.clerk_user_id == clerk_user_id)) is not None:
            raise SystemExit("Clerk user is already mapped; no changes made")
        db.add(User(clerk_user_id=clerk_user_id, role="employee", customer_id=None))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise SystemExit("Clerk user is already mapped") from None
    print("Employee mapping created")


if __name__ == "__main__":
    main()
