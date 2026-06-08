"""Bootstrap vendor repos into Python path.

Ensures cloned vendor repositories are importable without pip-installing
heavy dependency trees. Lightweight packages (legal-redline, contractguard)
are pip-installed; remaining repos are added to sys.path directly.
"""
import sys
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent.parent.parent.parent / "vendor"


def bootstrap() -> None:
    """Add vendor repo paths to sys.path."""
    paths_to_add = []

    # multi-agent-contract: agents live under apps/api
    mac_api = VENDOR_DIR / "multi-agent-contract" / "apps" / "api"
    if mac_api.exists():
        paths_to_add.append(str(mac_api))

    # graphrag-contract: modules at repo root
    grc = VENDOR_DIR / "graphrag-contract"
    if grc.exists():
        paths_to_add.append(str(grc))

    # agentic-rag: package under backend/
    ar = VENDOR_DIR / "agentic-rag"
    if ar.exists():
        paths_to_add.append(str(ar))

    # clauseiq: single-file app, not a package — no path needed

    # PageIndex: document tree builder
    pi = VENDOR_DIR / "PageIndex"
    if pi.exists():
        paths_to_add.append(str(pi))

    # Also add app/vendors/ for vendored packages copied into the backend
    vendors_dir = Path(__file__).resolve().parent.parent / "vendors"
    if vendors_dir.exists() and str(vendors_dir) not in sys.path:
        sys.path.insert(0, str(vendors_dir))

    # Prepend so vendor code shadows pip packages if needed
    for p in reversed(paths_to_add):
        if p not in sys.path:
            sys.path.insert(0, p)


bootstrap()
