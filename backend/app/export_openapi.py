"""python -m app.export_openapi > openapi.json  (contract consumed by the mobile client)."""

import json

from app.main import app

if __name__ == "__main__":
    print(json.dumps(app.openapi(), indent=2))
