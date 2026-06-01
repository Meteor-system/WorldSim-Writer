#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.devtools.e2e_cleanup import cleanup_e2e_data


def main() -> int:
    parser = argparse.ArgumentParser(description='Safely inspect or delete e2e-* users and associated worlds from a dev database.')
    parser.add_argument('--email-prefix', default='e2e-', help='Safe prefix to delete; must start with e2e-.')
    parser.add_argument('--confirm', action='store_true', help='Actually delete matched e2e-* data. Without this flag, only report matches.')
    args = parser.parse_args()

    db = SessionLocal()
    try:
        summary = cleanup_e2e_data(db, args.email_prefix, dry_run=not args.confirm)
    finally:
        db.close()

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
