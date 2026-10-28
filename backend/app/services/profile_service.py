import re
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.services.supabase_service import get_supabase, get_cv_bucket


def current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_profile_by_email(email: str) -> dict | None:
    if not email:
        return None

    cleaned_email = email.strip().lower()
    client = get_supabase()

    try:
        result = (
            client.table("profiles")
            .select("id, profile")
            .ilike("profile->>email", cleaned_email)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
    except Exception:
        # Fallback to in-memory check if json operator query fails
        all_rows = client.table("profiles").select("id, profile").execute()
        for row in all_rows.data or []:
            saved = row.get("profile") or {}
            if (saved.get("email") or "").strip().lower() == cleaned_email:
                return row

    return None


def get_profile_by_id(profile_id: str) -> dict:
    try:
        valid_id = str(UUID(profile_id))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="Profile not found.")

    client = get_supabase()
    try:
        result = (
            client.table("profiles")
            .select("*")
            .eq("id", valid_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query failed: {exc}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found.")

    row = result.data[0]
    return {
        "id": str(row["id"]),
        "profile": row.get("profile") or {},
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def create_profile_record(profile_data: dict, profile_id: str | None = None) -> str:
    client = get_supabase()
    new_id = profile_id or str(uuid4())

    try:
        result = (
            client.table("profiles")
            .insert({
                "id": new_id,
                "profile": profile_data,
            })
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Profile could not be created.")

    return new_id


def update_profile_record(profile_id: str, updates: dict) -> dict:
    current = get_profile_by_id(profile_id)
    valid_id = current["id"]
    existing_profile = current.get("profile") or {}

    merged_profile = {**existing_profile, **updates}
    if merged_profile.get("email"):
        merged_profile["email"] = merged_profile["email"].strip().lower()

    client = get_supabase()
    try:
        result = (
            client.table("profiles")
            .update({
                "profile": merged_profile,
                "updated_at": current_time(),
            })
            .eq("id", valid_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database update failed: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Profile update failed.")

    return {
        "message": "Profile updated successfully.",
        "id": valid_id,
        "profile": merged_profile,
    }


def upload_cv_file(
    profile_id: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> str:
    safe_filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    storage_path = f"{profile_id}/{uuid4().hex}_{safe_filename}"
    client = get_supabase()

    try:
        client.storage.from_(get_cv_bucket()).upload(
            storage_path,
            content,
            file_options={
                "content-type": content_type,
                "upsert": "false",
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Resume storage upload failed: {exc}",
        )

    return storage_path
