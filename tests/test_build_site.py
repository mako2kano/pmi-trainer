"""scripts/build_site.py（GitHub Pages 用の組み立て、DR-15）のテスト。"""

import json
import re

from scripts.build_site import build
from scripts.validate import REPO_ROOT, load_json


def _cached_assets(sw_text: str) -> list[str]:
    match = re.search(r"const ASSETS = (\[.*?\]);", sw_text, re.S)
    assert match, "sw.js に ASSETS が埋め込まれていない"
    return json.loads(match.group(1))


def test_site_contains_app_and_all_question_banks(tmp_path):
    out = tmp_path / "_site"
    build(out)
    assert (out / "index.html").exists()
    assert (out / "config" / "exams.json").exists()
    exams = load_json(REPO_ROOT / "config" / "exams.json")
    for exam_id, cfg in exams.items():
        for domain_id in cfg["domains"]:
            assert (out / "questions" / exam_id / f"{domain_id}.json").exists()


def test_service_worker_caches_every_served_file(tmp_path):
    out = tmp_path / "_site"
    build(out)
    sw = (out / "sw.js").read_text(encoding="utf-8")
    assert "__VERSION__" not in sw and "__ASSETS__" not in sw
    # 置換対象はコード中の1か所ずつだけ（コメントに書くと壊れる）
    assert sw.count("const ASSETS = [") == 1
    cached = set(_cached_assets(sw))
    served = {
        p.relative_to(out).as_posix()
        for p in out.rglob("*")
        if p.is_file() and p.name not in ("sw.js", ".nojekyll")
    }
    assert served <= cached


def test_cache_version_changes_when_content_changes(tmp_path):
    out = tmp_path / "_site"
    build(out)
    v1 = re.search(r"pmi-trainer-(\w+)", (out / "sw.js").read_text()).group(1)
    build(out)
    v2 = re.search(r"pmi-trainer-(\w+)", (out / "sw.js").read_text()).group(1)
    assert v1 == v2  # 中身が同じなら同じバージョン
