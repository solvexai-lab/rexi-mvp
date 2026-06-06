"""DOCX redline diff router — uses legal-redline-tools directly from vendor repo.
Accepts two .docx files and returns structured redline output.
"""
import os
import re
from fastapi import APIRouter, UploadFile, File, HTTPException
from legal_redline.diff import diff_documents

router = APIRouter(prefix="/api/v1/docx-diff", tags=["docx-diff"])


def _safe_filename(name: str) -> str:
    """Strip paths and unsafe characters from uploaded filenames."""
    base = os.path.basename(name)
    safe = re.sub(r"[^\w\-\.]", "_", base)
    return safe[:200]


@router.post("/compare")
async def compare_docx_files(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
):
    """Compare two .docx files and return redline-style differences.
    Uses literal legal-redline-tools diff algorithm (difflib.SequenceMatcher).
    """
    if not old_file.filename or not old_file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="old_file must be a .docx")
    if not new_file.filename or not new_file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="new_file must be a .docx")

    upload_dir = os.environ.get("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)

    old_path = os.path.join(upload_dir, f"diff_old_{_safe_filename(old_file.filename)}")
    new_path = os.path.join(upload_dir, f"diff_new_{_safe_filename(new_file.filename)}")

    with open(old_path, "wb") as f:
        f.write(await old_file.read())
    with open(new_path, "wb") as f:
        f.write(await new_file.read())

    try:
        changes = diff_documents(old_path, new_path, context_words=5)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Diff failed: {str(e)}")
    finally:
        # Cleanup temp files
        for p in [old_path, new_path]:
            try:
                os.remove(p)
            except Exception:
                pass

    return {
        "old_filename": old_file.filename,
        "new_filename": new_file.filename,
        "changes": changes,
        "summary": {
            "total_changes": len(changes),
            "replacements": len([c for c in changes if c.get("type") == "replace"]),
            "deletions": len([c for c in changes if c.get("type") == "delete"]),
            "insertions": len([c for c in changes if c.get("type") == "insert_after"]),
        }
    }
