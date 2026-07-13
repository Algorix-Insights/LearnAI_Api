from fastapi import APIRouter

# Answers are intentionally writable only through the authenticated attempt
# workflow in `resources/attempts.py`. Keeping this router empty prevents the
# generic CRUD surface from accepting grading fields or foreign attempt IDs.
router = APIRouter(prefix="/user-answers", tags=["exam-attempts"])
