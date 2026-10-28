import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Ensure .env is loaded from backend directory regardless of current working directory
_backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_backend_dir / ".env")
load_dotenv()

_supabase: Client | None = None


def get_max_cv_size_mb() -> int:
    return int(os.getenv("MAX_CV_SIZE_MB", "5"))


def get_cv_bucket() -> str:
    return os.getenv("SUPABASE_CV_BUCKET", "profile-cvs")


def get_supabase() -> Client:
    global _supabase

    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise RuntimeError(
                "Set SUPABASE_URL and SUPABASE_KEY in backend/.env"
            )

        _supabase = create_client(url, key)

    return _supabase
