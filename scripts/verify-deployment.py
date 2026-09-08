from __future__ import annotations

import re
import sys

import httpx


def main() -> int:
    base_url = sys.argv[1].rstrip("/")
    with httpx.Client(timeout=30) as client:
        page = client.get(base_url)
        print(f"html {page.status_code} {page.headers.get('content-type')}")
        print(page.text[:250].replace("\n", " "))
        assets = re.findall(r"""(?:src|href)=["']/([^"']+)""", page.text)
        assets = [asset for asset in assets if asset.startswith("assets/")]
        print(f"assets {assets}")
        ok = page.status_code == 200
        for asset in assets:
            response = client.get(f"{base_url}/{asset}")
            print(
                f"{asset} {response.status_code} "
                f"{response.headers.get('content-type')} {len(response.content)}"
            )
            ok = ok and response.status_code == 200
        return 0 if ok and assets else 1


if __name__ == "__main__":
    raise SystemExit(main())
