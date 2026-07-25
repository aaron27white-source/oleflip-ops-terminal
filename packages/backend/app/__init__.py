"""Put the Phase 1 (it-parts-system) engine on sys.path as soon as anything
under `app.` is imported, so service modules can `import calculator/db/models/
scanner` at module load time — before the FastAPI lifespan runs.
"""

import sys

from app.config import settings

if settings.phase1_path and settings.phase1_path not in sys.path:
    sys.path.insert(0, settings.phase1_path)
