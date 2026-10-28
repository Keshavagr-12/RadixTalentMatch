from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.profile_schema import ProfileCreate, ProfileUpdate
from app.services.profile_service import (
    create_profile_record,
    find_profile_by_email,
    get_profile_by_id,
    update_profile_record,
    upload_cv_file,
)
from app.services.resume_parser import extract_resume_data
from app.services.supabase_service import get_supabase
from app.utils.validators import validate_cv

router = APIRouter()


async def _handle_resume_upload(file: UploadFile, target_profile_id: str | None = None) -> dict:
    content = await validate_cv(file)
    filename = Path(file.filename or "resume.pdf").name
    extension = Path(filename).suffix.lower()

    try:
        extracted = extract_resume_data(content, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    existing_row = None
    if target_profile_id:
        existing_row = get_profile_by_id(target_profile_id)
        profile_id = str(existing_row["id"])
        action = "updated"
    elif extracted.get("email"):
        existing_row = find_profile_by_email(extracted["email"])
        if existing_row:
            profile_id = str(existing_row["id"])
            action = "updated"
        else:
            profile_id = None
            action = "created"
    else:
        profile_id = None
        action = "created"

    if existing_row:
        saved = existing_row.get("profile") or {}
        profile_data = {**saved}
        for key in ("name", "email", "education", "skills", "hackathons", "internships", "preferred_roles"):
            if extracted.get(key):
                profile_data[key] = extracted[key]
    else:
        profile_data = extracted

    # If profile_id is not yet known, create profile record to generate UUID
    if not profile_id:
        profile_id = create_profile_record(profile_data)

    # Upload original resume to Supabase Storage
    content_type = file.content_type or (
        "application/pdf"
        if extension == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    storage_path = upload_cv_file(
        profile_id=profile_id,
        filename=filename,
        content=content,
        content_type=content_type,
    )

    profile_data["cv_file"] = storage_path
    update_profile_record(profile_id, profile_data)

    return {
        "message": "Resume processed and profile saved successfully.",
        "action": action,
        "id": profile_id,
        "profile": profile_data,
    }


# --------------------------------------------------
# 1. Create a profile manually
# POST /api/profiles and POST /api/profiles/
# --------------------------------------------------
@router.post("", status_code=201)
@router.post("/", include_in_schema=False, status_code=201)
def create_profile(profile: ProfileCreate):
    data = profile.model_dump(mode="json")
    email = data.get("email", "").strip().lower()
    data["email"] = email

    if email:
        existing = find_profile_by_email(email)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="A profile with this email already exists. Open it to edit.",
            )

    profile_id = create_profile_record(data)

    return {
        "message": "Profile created successfully.",
        "id": profile_id,
        "profile": data,
    }


# --------------------------------------------------
# 2. List all profiles (with pagination)
# GET /api/profiles and GET /api/profiles/
# --------------------------------------------------
@router.get("", status_code=200)
@router.get("/", include_in_schema=False, status_code=200)
def list_profiles(limit: int = 50):
    client = get_supabase()
    try:
        result = (
            client.table("profiles")
            .select("id, profile, created_at, updated_at")
            .order("created_at", desc=True)
            .limit(min(limit, 100))
            .execute()
        )
        return result.data or []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list profiles: {exc}")


# --------------------------------------------------
# 3. Upload a resume without entering a profile ID
# POST /api/profiles/resume
# --------------------------------------------------
@router.post("/resume")
async def upload_resume_and_create_profile(
    file: UploadFile = File(...),
):
    return await _handle_resume_upload(file)


# --------------------------------------------------
# 4. Get a saved profile
# GET /api/profiles/{profile_id}
# --------------------------------------------------
@router.get("/{profile_id}")
def get_profile(profile_id: str):
    return get_profile_by_id(profile_id)


# --------------------------------------------------
# 5. Update a saved profile
# PUT /api/profiles/{profile_id}
# --------------------------------------------------
@router.put("/{profile_id}")
def update_profile(profile_id: str, updates: ProfileUpdate):
    update_data = updates.model_dump(mode="json", exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided for update.",
        )
    return update_profile_record(profile_id, update_data)


# --------------------------------------------------
# 6. Upload a resume to an existing profile
# POST /api/profiles/{profile_id}/resume
# --------------------------------------------------
@router.post("/{profile_id}/resume")
async def upload_resume_to_existing_profile(
    profile_id: str,
    file: UploadFile = File(...),
):
    return await _handle_resume_upload(file, target_profile_id=profile_id)
