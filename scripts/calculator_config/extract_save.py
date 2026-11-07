"""Read a decoded savegame into OUT/save_data.pkl (empire routes + per-area tables) for build_config.py.

Needs the decoded save in ANNO_DECODED (data_raw.xml and session_0..2.xml, see scripts/probes/README.md or the
--work-dir option of savegame_to_planner.py) and the layout repo (ANNO_LAYOUT_REPO) for savegame_to_planner.

    python extract_save.py [decoded-dir]
"""
import pickle
import sys
from pathlib import Path

import common

common.add_layout_repo_to_path()
import savegame_to_planner as s  # noqa: E402  (lives in the layout repo)


def main():
    decoded = Path(sys.argv[1]) if len(sys.argv) > 1 else common.DECODED
    outer = decoded / "data_raw.xml"
    guids = s.session_guids(outer)
    empire = s.read_empire(outer)
    print("empire", len(empire["routes"]), guids, flush=True)
    sessions = []
    for i in range(3):
        sessions.append(s.read_session(decoded / f"session_{i}.xml"))
        print("session", i, len(sessions[-1]), flush=True)
    for sess in sessions:
        for a in sess:
            a.pop("placed", None)
            a.pop("roads", None)
            a["itemMap"] = {}
    common.OUT.mkdir(parents=True, exist_ok=True)
    with open(common.SAVE_PKL, "wb") as fh:
        pickle.dump({"empire": empire, "sessions": sessions, "guids": guids}, fh)
    print("done", common.SAVE_PKL)


if __name__ == "__main__":
    main()
