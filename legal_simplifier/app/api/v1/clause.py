# """
# Single-clause detail endpoint
# GET /api/v1/clause/{uid}/{clause_id}
# """
# from fastapi import APIRouter, HTTPException
# from app.services.clause_ai_service import enrich_clause
# from app.services.document_store import get_clause_store

# router = APIRouter()

# # static lists for MVP – move to DB later
# LEGAL_AIDS = [
#     {"name": "Community Law Centre", "type": "community", "url": "https://communitylaw.example"},
#     {"name": "QuickCall Lawyer", "type": "private", "url": "https://quickcall.example"},
# ]

# VIDEO_SCRIPTS = {
#     "indemnity_unlimited": {
#         "title": "Unlimited indemnity – 15s explainer",
#         "script_lines": [
#             "Unlimited indemnity means you pay their lawyers forever.",
#             "Try to cap the amount or remove it.",
#         ],
#     },
# }

# @router.get("/clause/{uid}/{clause_id}")
# async def get_clause(uid: str, clause_id: int):
#     """
#     Return full clause tile compatible with HACK2SKILL spec
#     """
#     store = get_clause_store(uid)
#     clause = store.get(clause_id)
#     if not clause:
#         raise HTTPException(status_code=404, detail="Clause not found")

#     # enrich with AI-generated fields (eli5 + 3 rewrite options)
#     ai = await enrich_clause(
#         clause_text=clause["original_text"],
#         clause_type=clause["type"],
#     )

#     # inject static MVP helpers
#     clause.update(ai)
#     clause["community_rewrite"] = None  # placeholder
#     clause["legal_aids"] = LEGAL_AIDS
#     clause["video_script"] = VIDEO_SCRIPTS.get(
#         clause["type"],
#         {"title": "Clause explainer", "script_lines": ["Review this clause carefully."]},
#     )
#     return clause