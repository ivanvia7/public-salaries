import json
from pathlib import Path

import httpx
import respx

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "sf.json").read_text())
URL = "https://data.sf.gov/resource/88g8-5mnd.json"


@respx.mock
def test_check_source_command(run_cli):
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))

    code, out, _ = run_cli("check-source", "san_francisco")

    assert code == 0
    assert out == "ok san_francisco: 3 live rows read, 0 unreadable\n"
