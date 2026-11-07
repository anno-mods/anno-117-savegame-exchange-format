# savegame_to_planner: reference copy

`savegame_to_planner.py` and `README.md` are an unchanged copy of the layout tool's script. The canonical copy lives in
the Anno-117-Layout-Tool repository at `tools/savegame_to_planner/`; fixes go there.

## Not runnable from this folder

The script computes `LAYOUT_REPO = Path(__file__).resolve().parents[2]`, puts it on `sys.path` and then does

```python
import savegame_parser as sp        # <layout repo>/savegame_parser.py
import tool_manager                 # <layout repo>/tool_manager.py, only for the RdaConsole/FileDBReader lookup
```

So the file must sit at `<layout repo>/tools/savegame_to_planner/savegame_to_planner.py`. Run it from the layout repo
(or copy it there), not from this repository, where `parents[2]` is this repo root and the import fails.

Other scripts in this repository (`scripts/calculator_config/extract_save.py`) import the layout copy by putting
`<layout repo>/tools/savegame_to_planner` and `<layout repo>` on `sys.path`; the location comes from the environment
variable `ANNO_LAYOUT_REPO` (default `../Anno-117-Layout-Tool` next to this repository).

## Pointing it at the tools

| What | Option | Environment variable | Fallback |
|---|---|---|---|
| Layout repo | location of the script | `ANNO_LAYOUT_REPO` (only for `extract_save.py`) | `../Anno-117-Layout-Tool` |
| Planner repo (`paxplanner`) | `--planner-repo` | `ANNO_PLANNER_REPO` | `<layout repo>/../Anno-117-Planner` |
| RdaConsole.exe | `--rda-console` | `ANNO_RDACONSOLE` | `tool_manager.get_tool_paths` (settings, tools folder, PATH) |
| FileDBReader.exe | `--filedb-reader` | `ANNO_FILEDBREADER` | same |
| Game texts (island names) | `--texts texts_english.xml` | none | placeholder names (`Latium 5`) |

Example (run with the Planner repo's interpreter):

```
cd C:\dev\Anno-117-Planner
uv run python C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner\savegame_to_planner.py ^
    "<repo>\data\raw\saves\Marcia 69.a8s" -o marcia69.plan.json --plan-name "Marcia 69" ^
    --work-dir <repo>\outputs\decoded --report marcia69.report.json --texts <path>\texts_english.xml
```
