"""GitHub Pages 用のサイトを _site/ に組み立てる（DR-12・DR-15）。

app/（PWA本体）に、アプリが読む config/ と questions/ のJSONを同梱する。
service worker（app/sw.js）には、オフライン用にキャッシュするファイル一覧と、
中身から計算したバージョンを埋め込む。中身が変わればキャッシュも自動で更新される。

- 外部ライブラリに依存しない純粋Python
- CLI: python -m scripts.build_site [出力先（既定: _site）]
- ローカル確認: python -m scripts.build_site && python -m http.server -d _site 8000
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from scripts.validate import REPO_ROOT

APP_DIR = REPO_ROOT / "app"
DATA_DIRS = ("config", "questions")
SW_NAME = "sw.js"


def collect_files(repo_root: Path = REPO_ROOT) -> dict[str, Path]:
    """配信パス（_site/ からの相対） → 元ファイル の対応を返す。"""
    files: dict[str, Path] = {}
    for path in sorted((repo_root / "app").rglob("*")):
        if path.is_file() and path.name != ".DS_Store":
            files[path.relative_to(repo_root / "app").as_posix()] = path
    for name in DATA_DIRS:
        for path in sorted((repo_root / name).rglob("*.json")):
            files[path.relative_to(repo_root).as_posix()] = path
    return files


def site_version(files: dict[str, Path]) -> str:
    digest = hashlib.sha256()
    for rel, path in sorted(files.items()):
        digest.update(rel.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def render_sw(template: str, assets: list[str], version: str) -> str:
    return template.replace("__VERSION__", version).replace(
        "__ASSETS__", json.dumps(["./", *assets], ensure_ascii=False, indent=2)
    )


def build(out_dir: Path, repo_root: Path = REPO_ROOT) -> list[str]:
    """out_dir を作り直してサイトを組み立て、キャッシュ対象の一覧を返す。"""
    files = collect_files(repo_root)
    if "index.html" not in files or SW_NAME not in files:
        raise FileNotFoundError("app/index.html と app/sw.js が必要")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    for rel, src in files.items():
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel != SW_NAME:
            shutil.copyfile(src, dest)

    assets = [rel for rel in files if rel != SW_NAME]
    sw = render_sw(files[SW_NAME].read_text(encoding="utf-8"), assets, site_version(files))
    (out_dir / SW_NAME).write_text(sw, encoding="utf-8")
    # GitHub Pages の Jekyll 処理を無効にする（_ で始まるファイルも配信するため）
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    return assets


def main(argv: list[str]) -> int:
    out_dir = Path(argv[1]) if len(argv) > 1 else REPO_ROOT / "_site"
    assets = build(out_dir)
    print(f"OK: {out_dir} に {len(assets)} ファイルを組み立てた")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
