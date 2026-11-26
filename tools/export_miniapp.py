#!/usr/bin/env python3
"""把网站资料库数据导出给微信小程序「AI提示词助手」用。

用法：python3 tools/export_miniapp.py 小程序项目目录
生成 小程序目录/data/prompts.js、glossary.js（CommonJS 模块，打包进小程序，不联网）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build as B  # noqa: E402

out = Path(sys.argv[1]) / "data"
out.mkdir(parents=True, exist_ok=True)

issues = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "issues").glob("*.json"), reverse=True)
          if not f.stem.startswith("weekly")]

prompts = []
for d in issues:
    t = d.get("try")
    if t and t.get("prompt"):
        prompts.append({"id": f"i{d['issue']}", "cat": t.get("cat", "其他"), "title": t["title"], "intro": t.get("intro", ""),
                        "prompt": t["prompt"], "tip": t.get("tip", ""), "from": f"非常AI 第{d['issue']}期"})
for i, t in enumerate(json.loads((ROOT / "data" / "prompts_extra.json").read_text(encoding="utf-8"))):
    prompts.append({"id": f"x{i}", "cat": t.get("cat", "其他"), "title": t["title"], "intro": t.get("intro", ""),
                    "prompt": t["prompt"], "tip": t.get("tip", ""), "from": "常用精选"})
for p in prompts:
    if p["cat"] not in B.CATS:
        p["cat"] = "其他"
cats = []
for p in prompts:
    if p["cat"] not in cats:
        cats.append(p["cat"])
cat_meta = [{"name": c, "emoji": B.CATS[c][0], "color": B.CATS[c][1]} for c in cats]

words = [d["word"] for d in issues if d.get("word")]
have = {w["term"] for w in words}
words += [w for w in json.loads((ROOT / "data" / "glossary_extra.json").read_text(encoding="utf-8")) if w["term"] not in have]

stamp = B.latest_date()
(out / "prompts.js").write_text("module.exports = " + json.dumps({"updated": stamp, "cats": cat_meta, "list": prompts}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
(out / "glossary.js").write_text("module.exports = " + json.dumps({"updated": stamp, "list": words}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"exported {len(prompts)} prompts, {len(words)} words, data as of {stamp}")
