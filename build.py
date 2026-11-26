#!/usr/bin/env python3
"""非常AI 页面生成器。

每天出刊：
    python3 build.py issues/2026-11-25.json
从一期的 JSON 生成 news/日期.html 和首页 index.html（两页内容相同，只是相对路径不同）。
全站样式在 assets/site.css；改样式只改那个文件。

给存档、关于、核验记录页套上统一的页头页脚：
    python3 build.py wrap archive.html about.html verification-日期.html
只保留页面 <main> 里的内容，其余部分按当前模板重写。今日简报链接指向 issues/ 里最新一期。
"""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
E = html.escape
HOT = ' class="hot"'
CSS_V = hashlib.md5((ROOT / "assets" / "site.css").read_bytes()).hexdigest()[:8]

JS = """
document.querySelectorAll('.copy-btn').forEach(function(b){
  b.addEventListener('click',function(){
    var t=document.querySelector(b.dataset.copy).innerText;
    var done=function(){var o=b.textContent;b.textContent='已复制 ✓';setTimeout(function(){b.textContent=o},1600)};
    if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,function(){})}
  });
});
"""


def head(title, desc, url, base):
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:type" content="article"><meta property="og:site_name" content="非常AI">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://feichangai.vip/assets/og-cover.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="https://feichangai.vip/assets/og-cover.png">
<link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="{base}assets/site.css?v={CSS_V}"></head>
<body>
"""


def topbar(base, news_href, current):
    cur = lambda k: ' aria-current="page"' if k == current else ""
    return f"""<header><div class="wrap nav">
  <a class="logo" href="{base}index.html">非常<i>AI</i></a>
  <nav class="nav-links" aria-label="主导航"><a href="{base}index.html"{cur("home")}>首页</a><a href="{news_href}"{cur("news")}>今日简报</a><a href="{base}library.html"{cur("library")}>资料库</a><a href="{base}archive.html"{cur("archive")}>存档</a><a href="{base}about.html"{cur("about")}>关于</a></nav>
</div></header>
"""


def bottom(base, news_href):
    return f"""<footer><div class="wrap">
  <nav><a href="{base}index.html">首页</a><a href="{news_href}">今日简报</a><a href="{base}library.html">资料库</a><a href="{base}prompts.html">提示词库</a><a href="{base}topics.html">新闻搜索</a><a href="{base}archive.html">存档</a><a href="{base}about.html">关于</a></nav>
  非常AI · feichangai.vip<br>本站资讯均标注来源，只做自有摘要与点评并附原文链接，不全文转载。内容由 AI 辅助整理，逐条核对官方来源。
</div></footer>
"""


def links_html(pairs):
    return "<br>".join(
        f'<a href="{E(u)}" target="_blank" rel="noopener">{E(t)} ↗</a>' for t, u in pairs
    )


def render(d, base, current):
    """base: 到站点根目录的相对前缀（首页为''，news页为'../'）。current: 'home' 或 'news'。"""
    from pages import status_pill
    date = d["date"]
    _, m, dd = date.split("-")
    cn_date = f"{int(m)}月{int(dd)}日"
    news_href = f"{base}news/{date}.html"
    item = lambda i: (f"#{i}" if current == "news" else f"{news_href}#{i}")
    lead, flash = d["lead"], d["flash"]
    page_url = "https://feichangai.vip/" + ("" if current == "home" else f"news/{date}.html")

    toc = f'<li><a href="{item(lead["id"])}">{E(lead["title"])}</a></li>'
    toc += "".join(f'<li><a href="{item(f["id"])}">{E(f["title"])}</a></li>' for f in flash[:4])
    rest = len(flash) - 4
    more = (f"还有 {rest} 条快讯，" if rest > 0 else "") + "外加今天可以试试、好用工具、GitHub 精选、今日论文、AI小词典和模型榜单 👇"

    facts = "".join(
        f'<div class="fact"><span>{E(k)}</span><b{HOT if hot else ""}>{E(v)}</b></div>'
        for k, v, hot in lead["facts"]
    )
    paras = "".join(f"<p>{E(p)}</p>" for p in lead["paras"])
    flash_items = "".join(
        f'<li id="{f["id"]}"><h3><span class="em" aria-hidden="true">{f["emoji"]}</span><span>{E(f["title"])} {status_pill(f.get("status"))}</span></h3>'
        f'<p>{E(f["text"])}</p><div class="src"><span class="chip">{E(f["chip"])}</span>来源日期：{E(f["date"])} · '
        f'<a href="{E(f["url"])}" target="_blank" rel="noopener">原文 ↗</a></div></li>'
        for f in flash
    )
    t, p, b = d["try"], d["paper"], d["board"]
    rows = "".join(
        f'<tr><td class="rk">{i}</td><td>{E(r[0])}</td><td class="num">{E(r[1])}</td><td class="num">{E(r[2])}</td></tr>'
        for i, r in enumerate(b["rows"], 1)
    )
    title = f'{d["title"]} · 非常AI第{d["issue"]}期'
    minutes = d.get("minutes", 5)
    why = f'<div class="why"><b>💡 为什么重要</b>{E(lead["why"])}</div>' if lead.get("why") else ""
    fun = ""
    if d.get("fun"):
        f = d["fun"]
        fun = (f'<section class="card fun" id="{f.get("id", "fun")}"><div class="sec-title"><span class="em" aria-hidden="true">😄</span>今日趣闻</div>'
               f'<h3>{E(f["title"])}</h3><p>{E(f["text"])}</p><div class="src"><span class="chip">{E(f["chip"])}</span>来源日期：{E(f["date"])} · '
               f'<a href="{E(f["url"])}" target="_blank" rel="noopener">原文 ↗</a></div></section>')
    tools = ""
    if d.get("tools"):
        lis = "".join(
            f'<li><h4>{E(x["name"])}</h4><p>{E(x["desc"])}</p><p class="tag">{E(x["tag"])} · <a href="{E(x["url"])}" target="_blank" rel="noopener">官网 ↗</a></p></li>'
            for x in d["tools"])
        tools = (f'<section class="card" id="tools"><div class="sec-title"><span class="em" aria-hidden="true">🧰</span>好用工具</div>'
                 f'<ul class="tools-list">{lis}</ul></section>')
    repo = ""
    if d.get("repo"):
        r = d["repo"]
        how = f'<div class="prompt" id="repo-how">{E(r["how"])}</div><button class="copy-btn" data-copy="#repo-how">复制安装命令</button>' if r.get("how") else ""
        repo = (f'<section class="card repo" id="repo"><div class="sec-title"><span class="em" aria-hidden="true">🐙</span>GitHub 精选</div>'
                f'<h3>{E(r["name"])} <span class="kind">{E(r.get("kind", ""))}</span></h3><p>{E(r["desc"])}</p>'
                f'<p class="tip"><b>适合谁：</b>{E(r.get("who", ""))}</p>{how}'
                f'<div class="repo-meta"><span>📄 {E(r.get("license", "许可见仓库"))}</span><span>🕒 最近更新 {E(r.get("updated", ""))}</span><span>👤 {E(r.get("maintainer", ""))}</span></div>'
                f'<p class="tip">⚠️ {E(r.get("safety", "装之前先看一眼代码和需要的权限。"))}</p>'
                f'<div class="src"><a href="{E(r["url"])}" target="_blank" rel="noopener">GitHub 仓库 ↗</a></div></section>')
    word = ""
    if d.get("word"):
        w = d["word"]
        word = (f'<section class="card word" id="word"><div class="sec-title"><span class="em" aria-hidden="true">📖</span>AI小词典</div>'
                f'<h3><span class="term">{E(w["term"])}</span>{E(w["short"])}</h3><p>{E(w["plain"])}</p><p class="tip">举个例子：{E(w["example"])}</p></section>')

    body = f"""<main class="wrap">
<section class="hero">
  <span class="badge">第{d["issue"]}期 <b>{cn_date} {d["weekday"]}</b> · {minutes}分钟读完</span>
  <h1>{E(d["title"])}</h1>
  <p class="hello">{E(d["hello"])}</p>
</section>

{fun}

<nav class="card toc" aria-label="本期目录"><h2><span class="em" aria-hidden="true">📌</span>今天看什么</h2><ol>{toc}</ol><p class="more">{more}</p></nav>

<article class="card lead" id="{lead["id"]}">
  <div class="sec-title"><span class="em" aria-hidden="true">🔥</span>今日头条 {status_pill(lead.get("status"))}</div>
  <h2>{E(lead["title"])}</h2>
  <div class="tldr">{E(lead["tldr"])}</div>
  {paras}
  {why}
  <div class="facts">{facts}</div>
  <div class="src"><span class="chip">{E(lead["chip"])}</span><br>来源日期：{E(lead["date"])}<br>{links_html(lead["links"])}</div>
</article>

<section class="card" id="flash">
  <div class="sec-title"><span class="em" aria-hidden="true">⚡</span>快讯</div>
  <ul class="flash-list">{flash_items}</ul>
</section>

<section class="card try" id="try">
  <div class="sec-title"><span class="em" aria-hidden="true">🧪</span>今天可以试试</div>
  <h3>{E(t["title"])}</h3>
  <p>{E(t["intro"])}</p>
  <div class="prompt" id="prompt-text">{E(t["prompt"])}</div>
  <button class="copy-btn" data-copy="#prompt-text">复制提示词</button>
  <p class="tip">💡 {E(t["tip"])}</p>
</section>

{tools}

{repo}

<section class="card paper" id="paper">
  <div class="sec-title"><span class="em" aria-hidden="true">📄</span>今日论文</div>
  <h3>{E(p["title"])}</h3>
  <p>{E(p["text"])}</p>
  <p class="pname">{E(p["name"])}（{E(p["date"])}）</p>
  <div class="src"><a href="{E(p["url"])}" target="_blank" rel="noopener">论文页面 ↗</a></div>
</section>

{word}

<section class="card" id="board">
  <div class="sec-title"><span class="em" aria-hidden="true">🏆</span>{E(b["title"])}</div>
  <table><thead><tr><th>#</th><th>模型</th><th class="num">得分</th><th class="num">每题成本</th></tr></thead><tbody>{rows}</tbody></table>
  <p class="note">{E(b["note"])} <a href="{E(b["url"])}" target="_blank" rel="noopener">完整榜单 ↗</a></p>
</section>

<div class="end"><p class="bye">今天就到这儿，明天见 👋</p>
<p>觉得有用，就转发给一个也在关注 AI 的朋友 🙌</p>
<p>每条都核对过官方原文。<a href="{base}verification-{date}.html">本期核验记录</a> · <a href="{base}archive.html">往期存档</a></p></div>
</main>
"""
    return (head(title, d["description"], page_url, base) + topbar(base, news_href, current)
            + body + bottom(base, news_href) + f"<script>{JS}</script>\n</body></html>\n")


CATS = {  # 分类：emoji、主色、浅底色
    "工作": ("💼", "#6b4eff", "var(--violet-bg)"),
    "生活": ("🏠", "#ff5a36", "var(--coral-bg)"),
    "办事": ("📋", "#12a37a", "var(--mint-bg)"),
    "学习": ("📚", "#2f80ed", "#e8f1fd"),
    "写作": ("✍️", "#d9480f", "var(--sun-bg)"),
    "成长": ("🌱", "#12a37a", "var(--mint-bg)"),
    "编程": ("💻", "#1d1b26", "#ecebf0"),
    "其他": ("✨", "#6b4eff", "var(--violet-bg)"),
}

def latest_date():
    return sorted(p.stem for p in (ROOT / "issues").glob("*.json") if not p.stem.startswith("weekly"))[-1]


def wrap(name):
    """给存档／关于／核验页套统一外壳，只保留 <main> 内的内容。"""
    f = ROOT / name
    s = f.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", s, re.S).group(1).strip()
    m = re.search(r'<meta name="description" content="(.*?)"', s)
    desc = html.unescape(m.group(1)) if m else "非常AI · 每天几条值得关注的 AI 变化，中文讲清，标好来源与限制。"
    inner = re.search(r"<main[^>]*>(.*)</main>", s, re.S).group(1)
    inner = re.sub(r'^\s*<a href="index.html">返回首页</a>', "", inner)
    inner = inner.replace("<pre>", '<pre class="log">')
    current = {"archive.html": "archive", "about.html": "about"}.get(name, "")
    news_href = f"news/{latest_date()}.html"
    out = (head(html.unescape(title), desc, f"https://feichangai.vip/{name}", "")
           + topbar("", news_href, current)
           + f'<main class="wrap page">{inner}</main>\n' + bottom("", news_href) + "</body></html>\n")
    f.write_text(out, encoding="utf-8")


def main():
    if sys.argv[1] in ("pages", "prompts"):
        import pages
        print("built pages", pages.build_all())
        return
    if sys.argv[1] == "wrap":
        for n in sys.argv[2:]:
            wrap(n)
            print("wrapped", n)
        return
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT
    d = json.loads(src.read_text(encoding="utf-8"))
    (out / "news").mkdir(parents=True, exist_ok=True)
    (out / "news" / f'{d["date"]}.html').write_text(render(d, "../", "news"), encoding="utf-8")
    (out / "index.html").write_text(render(d, "", "home"), encoding="utf-8")
    import pages
    counts = pages.build_all()
    print("built", d["date"], "+ pages", counts, "->", out)


if __name__ == "__main__":
    main()
