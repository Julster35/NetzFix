"""Command line: `netzfix build` (data + grid + assets), `netzfix serve` (playground)."""

from __future__ import annotations

import argparse


def main() -> None:
    p = argparse.ArgumentParser(prog="netzfix")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="download inputs and build grid, demand and baseline assets")
    s = sub.add_parser("serve", help="start the local playground (API + web UI)")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--host", default="127.0.0.1")
    a = p.parse_args()

    if a.cmd == "build":
        from netzfix.data import mastr, regions, smard
        from netzfix.network import assets, grid

        smard.build_year(2024)
        regions.build(2024)
        regions.lau_points(2024)
        grid.save(grid.build())
        mastr.download()
        mastr.register_zip()
        if not (mastr.DATA_PROCESSED / "mastr_units_20261103.parquet").exists():
            mastr.parse()
        print(assets.build())
    elif a.cmd == "serve":
        import uvicorn

        uvicorn.run("netzfix.server.app:app", host=a.host, port=a.port)


if __name__ == "__main__":
    main()
