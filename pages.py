"""非常AI 资料库页面：资料库总入口、提示词库、工具箱、AI小词典、新闻话题与搜索、模型价格、新手入门、每周回顾。

全部从 issues/*.json 和 data/*.json 自动生成，由 build.py 调用。
"""
import json
import re

import build as B

E = B.E

# ---------- 共用 ----------

STATUS = {  # 状态标签：底色、文字色（深浅色都看得清）
    "已上线": ("#e3f6ee", "#0f8a63"),
    "测试中": ("#fff3d6", "#a36500"),
    "部分开放": ("#e5efff", "#2f6fd6"),
    "需排队": ("#fff3d6", "#a36500"),
    "仅预告": ("#ffe9e3", "#d63c1a"),
    "可下载": ("#efeaff", "#5b3fe0"),
    "研究": ("#eeedf2", "#5c5866"),
    "观点": ("#eeedf2", "#5c5866"),
}
STATUS_HELP = {
    "已上线": "现在就能用（可能限地区或付费）",
    "测试中": "公开测试或 beta，功能可能会变",
    "部分开放": "只对部分用户、套餐或渠道开放",
    "需排队": "要申请或排队等名额",
    "仅预告": "公司宣布了，但还没开放",
    "可下载": "开源或开放权重，模型可以下载",
    "研究": "论文或实验结果，不是产品",
    "观点": "公司或人物的说法、提议",
}


def status_pill(s):
    if not s or s not in STATUS:
        return ""
    bg, fg = STATUS[s]
    return f'<span class="st" style="background:{bg};color:{fg}">{E(s)}</span>'


TAG_RULES = [  # 话题：关键词（不分大小写）
    ("OpenAI", ["openai", "chatgpt", "gpt-", "codex", "sora"]),
    ("Google", ["google", "gemini", "deepmind", "workspace"]),
    ("Anthropic", ["anthropic", "claude"]),
    ("Meta", ["meta ", "meta的", "llama", "muse "]),
    ("微软", ["微软", "microsoft", "copilot"]),
    ("英伟达", ["英伟达", "nvidia"]),
    ("阿里", ["阿里", "qwen", "通义"]),
    ("智谱", ["智谱", "glm"]),
    ("DeepSeek", ["deepseek"]),
    ("字节", ["字节", "豆包", "seedream", "doubao"]),
    ("百度", ["百度", "ernie", "文心"]),
    ("腾讯", ["腾讯", "混元", "hy4"]),
    ("月之暗面", ["月之暗面", "kimi"]),
    ("MiniMax", ["minimax"]),
    ("商汤", ["商汤", "sensenova"]),
    ("开源", ["开源", "开放权重", "权重", "apache", "mit 许可"]),
    ("编程", ["编程", "写代码", "代码", "coding", "devin"]),
    ("智能体", ["智能体", "agent", "mcp"]),
    ("图片视频", ["生图", "画图", "图片", "视频", "image"]),
    ("价格", ["降价", "涨价", "每百万 token", "价格"]),
    ("安全隐私", ["网络安全", "漏洞", "隐私", "数据留存", "滥用", "个人信息"]),
    ("研究", ["论文", "研究", "实验", "定理", "证明"]),
]
DOMESTIC = {"阿里", "智谱", "DeepSeek", "字节", "百度", "腾讯", "月之暗面", "MiniMax", "商汤"}


def tags_for(item):
    text = " ".join([item.get("title", ""), item.get("text", ""), item.get("tldr", ""),
                     " ".join(item.get("paras", []))]).lower()
    tags = [t for t, kws in TAG_RULES if any(k in text for k in kws)]
    for t in item.get("tags", []):
        if t not in tags:
            tags.append(t)
    if any(t in DOMESTIC for t in tags) and "国内厂商" not in tags:
        tags.append("国内厂商")
    return tags


def issues():
    out = []
    for f in sorted((B.ROOT / "issues").glob("*.json"), reverse=True):
        if f.stem.startswith("weekly"):
            continue
        out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def weeklies():
    out = []
    for f in sorted((B.ROOT / "issues").glob("weekly-*.json"), reverse=True):
        out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


LIB_JS = """
(function(){
  var cards=[].slice.call(document.querySelectorAll('[data-cat]')).filter(function(c){return !c.classList.contains('chip-btn')});
  var q=document.getElementById('q'),cat='全部',empty=document.querySelector('.empty');
  function apply(){var k=(q?q.value:'').trim().toLowerCase(),n=0;
    cards.forEach(function(c){var cs=(c.dataset.cat||'').split('|');var ok=(cat==='全部'||cs.indexOf(cat)>-1)&&(!k||c.innerText.toLowerCase().indexOf(k)>-1);c.style.display=ok?'':'none';if(ok)n++;});
    if(empty)empty.style.display=n?'none':'block';}
  document.querySelectorAll('.chip-btn').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('.chip-btn').forEach(function(x){x.setAttribute('aria-pressed','false')});
    b.setAttribute('aria-pressed','true');cat=b.dataset.cat;apply();});});
  if(q){q.addEventListener('input',apply);}
  function fromHash(){var h=decodeURIComponent((location.hash||'').slice(1));if(h){var b=document.querySelector('.chip-btn[data-cat="'+h+'"]');if(b){b.click();window.scrollTo({top:0,behavior:'smooth'});}}}
  fromHash();window.addEventListener('hashchange',fromHash);
  document.querySelectorAll('.mini-copy').forEach(function(b){b.addEventListener('click',function(){
    var t=document.getElementById(b.dataset.src).textContent;
    if(navigator.clipboard){navigator.clipboard.writeText(t).then(function(){var o=b.textContent;b.textContent='已复制 ✓';setTimeout(function(){b.textContent=o},1500)})}});});
})();
"""


def chips_html(cats, labels=None):
    labels = labels or {}
    return ('<button class="chip-btn" aria-pressed="true" data-cat="全部">全部</button>' + "".join(
        f'<button class="chip-btn" aria-pressed="false" data-cat="{E(c)}">{E(labels.get(c, c))}</button>' for c in cats))


def lib_page(slug, title, emoji, lede, count, body, desc, search_ph=None, chips="", note=""):
    news_href = f"news/{B.latest_date()}.html"
    search = (f'<label class="search"><span aria-hidden="true">🔍</span><input id="q" type="search" '
              f'placeholder="{E(search_ph)}" aria-label="搜索"></label>') if search_ph else ""
    chips = f'<div class="chips" role="group" aria-label="按分类筛选">{chips}</div>' if chips else ""
    main = f"""<main class="wrap">
<nav class="crumb"><a href="library.html">资料库</a> / {E(title)}</nav>
<section class="lib-head"><h1>{emoji} {E(title)}</h1><p>{lede}</p>{f'<span class="count">{count}</span>' if count else ''}</section>
{search}{chips}
{body}
<p class="empty">没有找到，换个词试试 🙂</p>
{f'<p class="lib-note">{note}</p>' if note else ''}
</main>
"""
    html_out = (B.head(f"{title} · 非常AI", desc, f"https://feichangai.vip/{slug}.html", "")
                + B.topbar("", news_href, "library") + main + B.bottom("", news_href)
                + f"<script>{LIB_JS}</script>\n</body></html>\n")
    (B.ROOT / f"{slug}.html").write_text(html_out, encoding="utf-8")


# ---------- 提示词库 ----------

def build_prompts(all_issues):
    items = [(d, d["try"]) for d in all_issues if d.get("try", {}).get("prompt")]
    used, cards = [], ""
    for d, t in items:
        cat = t.get("cat", "其他")
        if cat not in B.CATS:
            cat = "其他"
        if cat not in used:
            used.append(cat)
        emo, color, bg = B.CATS[cat]
        pid = f"p{d['issue']}"
        cards += f"""<article class="pcard" data-cat="{cat}" style="--accent:{color};--accent-bg:{bg}">
<div class="top"></div><div class="inner">
<div class="row"><div class="ico" aria-hidden="true">{emo}</div><div><span class="tag">{cat}</span><h3>{E(t["title"])}</h3></div></div>
<p style="font-size:14px;color:var(--soft)">{E(t.get("intro", ""))}</p>
<details><summary>展开完整提示词 ▾</summary><div class="preview">{E(t["prompt"])}</div><pre id="{pid}">{E(t["prompt"])}</pre></details>
<div class="foot"><span>第{d["issue"]}期 · <a href="news/{d["date"]}.html#try">原文</a> · 适用于豆包、DeepSeek、Kimi、ChatGPT 等</span>
<button class="mini-copy" data-src="{pid}">复制</button></div>
</div></article>
"""
    extra = json.loads((B.ROOT / "data" / "prompts_extra.json").read_text(encoding="utf-8"))
    for i, t in enumerate(extra):
        cat = t.get("cat", "其他") if t.get("cat") in B.CATS else "其他"
        if cat not in used:
            used.append(cat)
        emo, color, bg = B.CATS[cat]
        pid = f"px{i}"
        cards += f"""<article class="pcard" data-cat="{cat}" style="--accent:{color};--accent-bg:{bg}">
<div class="top"></div><div class="inner">
<div class="row"><div class="ico" aria-hidden="true">{emo}</div><div><span class="tag">{cat}</span><h3>{E(t["title"])}</h3></div></div>
<p style="font-size:14px;color:var(--soft)">{E(t.get("intro", ""))}</p>
<details><summary>展开完整提示词 ▾</summary><div class="preview">{E(t["prompt"])}</div><pre id="{pid}">{E(t["prompt"])}</pre></details>
<p style="font-size:13px;color:var(--mute)">💡 {E(t.get("tip", ""))}</p>
<div class="foot"><span>常用精选 · 适用于豆包、DeepSeek、Kimi、ChatGPT 等</span>
<button class="mini-copy" data-src="{pid}">复制</button></div>
</div></article>
"""
    items = items + extra
    lib_page("prompts", "提示词库", "🧪", "每期「今天可以试试」都收在这里。挑一个，点复制，贴给你常用的 AI 就能用。",
             f"已收录 {len(items)} 条 · 每天更新", f'<div class="grid">{cards}</div>',
             "非常AI提示词库：每天一个拿来就能用的AI提示词，适用于豆包、DeepSeek、Kimi、ChatGPT等，一键复制。",
             "搜一搜：合同、做饭、复盘……", chips_html(used, {c: f"{B.CATS[c][0]} {c}" for c in used}),
             "小提示：方括号里的内容换成你自己的情况。涉及健康、法律、钱的问题，AI 的回答只能参考，不能代替专业人士。")
    return len(items)


# ---------- 工具箱 ----------

TOOL_CATS = {"编程": "💻", "智能体": "🤖", "图片": "🎨", "视频": "🎬", "写作": "✍️", "办公": "📊",
             "学习": "📚", "隐私安全": "🔒", "其他": "🧩"}


def build_tools(all_issues):
    rows = []
    for d in all_issues:
        for t in d.get("tools", []):
            rows.append((d, t))
    used, cards = [], ""
    for d, t in rows:
        cat = t.get("cat", "其他")
        if cat not in TOOL_CATS:
            cat = "其他"
        if cat not in used:
            used.append(cat)
        cards += f"""<article class="pcard" data-cat="{cat}" style="--accent:var(--coral);--accent-bg:var(--coral-bg)">
<div class="top"></div><div class="inner">
<div class="row"><div class="ico" aria-hidden="true">{TOOL_CATS[cat]}</div><div><span class="tag">{cat}</span><h3>{E(t["name"])}</h3></div></div>
<p style="font-size:15px">{E(t["desc"])}</p>
<p class="preview" style="-webkit-line-clamp:unset">{E(t["tag"])}</p>
<div class="foot"><span>第{d["issue"]}期推荐 · <a href="news/{d["date"]}.html#tools">原文</a></span>
<a class="mini-copy" style="text-decoration:none" href="{E(t["url"])}" target="_blank" rel="noopener">官网 ↗</a></div>
</div></article>
"""
    lib_page("tools", "AI 工具箱", "🧰", "每期「好用工具」都收在这里：给谁用、能干什么、收不收费、支持什么系统，一眼看清。",
             f"已收录 {len(rows)} 个 · 每天更新", f'<div class="grid">{cards}</div>',
             "非常AI工具箱：每天推荐的新AI工具汇总，标清免费还是付费、支持的系统、国内能否使用。",
             "搜一搜：写代码、视频、Mac……", chips_html(used, {c: f"{TOOL_CATS[c]} {c}" for c in used}),
             "工具信息以推荐当天的官网为准，价格和功能之后可能变化。本站推荐不收费。")
    return len(rows)


# ---------- 开源精选 ----------

def build_repos(all_issues):
    rows = [(d, d["repo"]) for d in all_issues if d.get("repo")]
    seen = {r["url"] for _, r in rows}
    extra = [r for r in json.loads((B.ROOT / "data" / "repos_extra.json").read_text(encoding="utf-8")) if r["url"] not in seen]
    kinds, cards = [], ""
    for d, r in rows + [(None, r) for r in extra]:
        k = r.get("kind") or "项目"
        if k not in kinds:
            kinds.append(k)
        src = f'第{d["issue"]}期推荐 · <a href="news/{d["date"]}.html#repo">原文</a>' if d else f'精选 · 核对于 {E(r.get("added", ""))}'
        how = f'<pre>{E(r["how"])}</pre>' if r.get("how") else ""
        cards += f"""<article class="pcard" data-cat="{E(k)}" style="--accent:var(--ink);--accent-bg:var(--bg)">
<div class="top"></div><div class="inner">
<div class="row"><div class="ico" aria-hidden="true">🐙</div><div><span class="tag">{E(k)}</span><h3 style="overflow-wrap:anywhere">{E(r["name"])}</h3></div></div>
<p style="font-size:15px">{E(r["desc"])}</p>
<p style="font-size:14px;color:var(--soft)"><b>适合谁：</b>{E(r.get("who", ""))}</p>{how}
<p class="preview" style="-webkit-line-clamp:unset">📄 {E(r.get("license", ""))} · 🕒 {E(r.get("updated", ""))} · 👤 {E(r.get("maintainer", ""))}<br>⚠️ {E(r.get("safety", ""))}</p>
<div class="foot"><span>{src}</span><a class="mini-copy" style="text-decoration:none" href="{E(r["url"])}" target="_blank" rel="noopener">GitHub ↗</a></div>
</div></article>
"""
    lib_page("repos", "GitHub 开源精选", "🐙", "每期「GitHub 精选」都收在这里：好用的 Skill、MCP 服务器和 AI 开源项目，写清许可、维护情况和安全提醒。",
             f"已收录 {len(rows) + len(extra)} 个 · 每天更新", f'<div class="grid">{cards}</div>',
             "非常AI GitHub开源精选：每天推荐一个靠谱的AI Skill、MCP服务器或开源项目，标清许可证、更新时间和安全提醒。",
             "搜一搜：Skill、MCP、Claude……", chips_html(kinds),
             "Skill 和 MCP 服务器可能会在你的电脑上运行代码、读写文件。安装前先看代码、限制权限；本站推荐不收费。")
    return len(rows) + len(extra)


# ---------- AI 小词典 ----------

def build_glossary(all_issues):
    words = [(d, d["word"]) for d in all_issues if d.get("word")]
    cards = ""
    for d, w in words:
        cards += f"""<article class="pcard" data-cat="词" style="--accent:var(--ink);--accent-bg:var(--bg)">
<div class="top"></div><div class="inner">
<h3><span class="term-tag">{E(w["term"])}</span> {E(w["short"])}</h3>
<p style="font-size:15px">{E(w["plain"])}</p>
<p class="preview" style="-webkit-line-clamp:unset">举个例子：{E(w["example"])}</p>
<div class="foot"><span>第{d["issue"]}期 · <a href="news/{d["date"]}.html#word">原文</a></span></div>
</div></article>
"""
    have = {w["term"] for _, w in words}
    extra = [w for w in json.loads((B.ROOT / "data" / "glossary_extra.json").read_text(encoding="utf-8")) if w["term"] not in have]
    for w in extra:
        cards += f"""<article class="pcard" data-cat="词" style="--accent:var(--ink);--accent-bg:var(--bg)">
<div class="top"></div><div class="inner">
<h3><span class="term-tag">{E(w["term"])}</span> {E(w["short"])}</h3>
<p style="font-size:15px">{E(w["plain"])}</p>
<p class="preview" style="-webkit-line-clamp:unset">举个例子：{E(w["example"])}</p>
<div class="foot"><span>基础词条</span></div>
</div></article>
"""
    words = words + [(None, w) for w in extra]
    lib_page("glossary", "AI 小词典", "📖", "新闻里看不懂的 AI 词，这里用大白话讲清楚。每天新增一个。",
             f"已收录 {len(words)} 个词 · 每天更新", f'<div class="grid">{cards}</div>',
             "非常AI小词典：用大白话解释 token、智能体、开放权重等常见AI术语，每天新增一个。",
             "搜一搜：token、智能体……")
    return len(words)


# ---------- 新闻话题与搜索 ----------

def build_topics(all_issues):
    rows, tag_count = [], {}
    for d in all_issues:
        items = [d["lead"]] + d["flash"]
        for x in items:
            tags = tags_for(x)
            for t in tags:
                tag_count[t] = tag_count.get(t, 0) + 1
            summary = x.get("tldr") or x.get("text", "")
            rows.append((d, x, tags, summary))
    for x in json.loads((B.ROOT / "data" / "legacy_news.json").read_text(encoding="utf-8")):
        tags = tags_for(x)
        for t in tags:
            tag_count[t] = tag_count.get(t, 0) + 1
        d = {"date": x["date"], "issue": x["issue"]}
        rows.append((d, x, tags, x["text"]))
    order = sorted(tag_count, key=lambda t: (-tag_count[t], t))
    cards = ""
    for d, x, tags, summary in rows:
        lead = x["id"] == "item-01"
        tag_html = "".join(f'<a class="ttag" href="#{E(t)}">#{E(t)}</a>' for t in tags)
        url = x.get("url") or (x.get("links") or [["", ""]])[0][1]
        cards += f"""<article class="ncard" data-cat="{E('|'.join(tags))}">
<div class="nmeta">{status_pill(x.get("status"))}{'<span class="st" style="background:var(--coral-bg);color:var(--coral)">头条</span>' if lead else ''}<span>{d["date"]} · 第{d["issue"]}期</span></div>
<h3><a href="news/{d["date"]}.html#{x["id"]}">{E(x["title"])}</a></h3>
<p>{E(summary[:150])}{'…' if len(summary) > 150 else ''}</p>
<div class="nfoot">{tag_html}{f'<a class="src-a" href="{E(url)}" target="_blank" rel="noopener">原文 ↗</a>' if url else ''}</div>
</article>
"""
    labels = {t: f"{t} {tag_count[t]}" for t in order}
    lib_page("topics", "新闻话题与搜索", "🔎", "往期所有新闻都在这里。按公司或话题筛选，或者直接搜关键词。",
             f"共 {len(rows)} 条新闻 · {len(order)} 个话题", f'<div class="nlist">{cards}</div>',
             "非常AI往期新闻搜索：按 OpenAI、Google、Anthropic、国内厂商、开源等话题筛选。",
             "搜一搜：Claude、开源、降价……", chips_html(order, labels),
             "状态标签说明：" + "；".join(f"{k}＝{v}" for k, v in STATUS_HELP.items()) + "。")
    return len(rows)


# ---------- 模型价格 ----------

def build_prices():
    data = json.loads((B.ROOT / "data" / "prices.json").read_text(encoding="utf-8"))
    vendors = []
    trs = ""

    def fmt(v, cur):
        if v is None:
            return "—"
        sym = "$" if cur == "USD" else "¥"
        s = f"{v:.3f}".rstrip("0").rstrip(".") if v < 1 else f"{v:.2f}".rstrip("0").rstrip(".")
        return sym + s

    for r in data["rows"]:
        if r["vendor"] not in vendors:
            vendors.append(r["vendor"])
        trs += f"""<tr data-cat="{E(r["vendor"])}"><td><b>{E(r["model"])}</b><span class="sub">{E(r["vendor"])}{(' · ' + E(r["id"])) if r["id"] else ''}</span></td>
<td class="num">{fmt(r["input"], r["cur"])}</td><td class="num"><b>{fmt(r["output"], r["cur"])}</b></td><td class="num">{fmt(r["cached"], r["cur"])}</td>
<td class="pnote">{E(r["note"])} <a href="{E(r["src"])}" target="_blank" rel="noopener">来源 ↗</a></td></tr>
"""
    body = f"""<div class="ptable-wrap"><table class="ptable"><thead><tr><th>模型</th><th class="num">输入</th><th class="num">输出</th><th class="num">缓存输入</th><th>说明</th></tr></thead>
<tbody>{trs}</tbody></table></div>"""
    lib_page("prices", "大模型 API 价格表", "💰",
             "主流大模型的 API 价格对比：喂给模型的「输入」、重复内容的「缓存输入」、模型写出来的「输出」，单位都是每百万 token。",
             f"核对日期 {data['checked']} · 有调价随新闻更新", body,
             "主流大模型API价格对比表：GPT-6.2、Claude、Gemini 4、DeepSeek、Qwen 每百万token输入输出价格，附官方来源。",
             None, chips_html(vendors),
             E(data["note"]) + " $ 为美元，¥ 为人民币。不知道 token 是什么？看 <a href=\"glossary.html\">AI 小词典</a>。")


# ---------- 新手入门 ----------

def build_start():
    body = """<div class="article">
<h2>1. AI 现在能帮你做什么</h2>
<p>最常用的是「聊天 AI」：你打字问，它打字答。能帮你写东西（文案、邮件、总结）、解释看不懂的内容（合同、通知、说明书）、出主意（做饭、旅行、学习计划）、写代码，很多还能看图、听语音、画画。</p>
<h2>2. 先从哪个开始</h2>
<p>手机应用商店里搜「AI 助手」就能找到很多，国内常见的有豆包、DeepSeek、Kimi 等，下载一个注册就能聊。先挑一个用熟，比到处换更有用。我们每天的新闻里，会写清新功能在国内能不能直接用。</p>
<h2>3. 怎么跟 AI 说话，回答才好</h2>
<p>把它当成一个聪明但不了解你的新同事，说清楚四件事：</p>
<ul><li><b>你是谁、什么情况</b>：比如「我家三口人，孩子 8 岁」。</li>
<li><b>要它做什么</b>：比如「帮我排 5 天晚饭」。</li>
<li><b>要什么样的结果</b>：比如「列成表格，附买菜清单」。</li>
<li><b>有什么限制</b>：比如「每顿不超过 30 分钟，不吃辣」。</li></ul>
<p>不满意就接着说「再短一点」「换个说法」，它会改。懒得自己想？去 <a href="prompts.html">提示词库</a> 挑一个现成的，复制就能用。</p>
<h2>4. 用 AI 要注意的三件事</h2>
<ul><li><b>它会一本正经地说错</b>（这叫「幻觉」）。重要的数字、日期、政策，要自己再查一下。</li>
<li><b>别把隐私贴进去</b>：身份证号、银行卡号、密码、病历原件，能不贴就不贴。</li>
<li><b>健康、法律、钱的事</b>，AI 的回答只能参考，不能代替医生、律师和专业人士。</li></ul>
<h2>5. 怎么看「非常AI」</h2>
<p>我们每天早上出一期 <a href="index.html">AI 日报</a>：一条头条讲透，再加几条快讯，还有提示词、好用工具、论文、小词典和模型榜单，大约 7 分钟看完。每条新闻都核对过官方原文，旁边的小标签告诉你它现在到哪一步了：</p>
<div class="st-legend">STATUS_LEGEND</div>
<p>看到不懂的词，查 <a href="glossary.html">AI 小词典</a>；想找以前的新闻，用 <a href="topics.html">新闻搜索</a>。</p>
</div>"""
    legend = "".join(f'<p>{status_pill(k)} {E(v)}</p>' for k, v in STATUS_HELP.items())
    body = body.replace("STATUS_LEGEND", legend)
    lib_page("start", "AI 新手入门", "👋", "第一次用 AI？花 3 分钟看完这页，就知道从哪开始、怎么问、要注意什么。",
             "", body, "AI新手入门：AI能做什么、先用哪个、怎么写提示词、要注意什么，以及怎么看非常AI日报。")


# ---------- 每周回顾 ----------

def build_weekly_pages():
    ws = weeklies()
    news_href = f"news/{B.latest_date()}.html"
    (B.ROOT / "weekly").mkdir(exist_ok=True)
    for w in ws:
        tops = "".join(f"""<li><h3><a href="../news/{E(t["date"])}.html#{E(t.get("anchor", "item-01"))}">{E(t["title"])}</a></h3>
<p>{E(t["text"])}</p><p class="wmeta">{status_pill(t.get("status"))} 第{E(str(t.get("issue", "")))}期 · {E(t["date"])}</p></li>""" for t in w["top"])
        extra = ""
        for key, label in (("prompt_pick", "🧪 本周最实用的提示词"), ("tool_pick", "🧰 本周最值得试的工具"), ("trend", "📈 本周趋势")):
            if w.get(key):
                extra += f'<section class="card"><div class="sec-title">{label}</div><p>{E(w[key])}</p></section>'
        body = f"""<main class="wrap">
<nav class="crumb"><a href="../library.html">资料库</a> / <a href="../weekly.html">每周回顾</a></nav>
<section class="hero"><span class="badge">每周回顾 <b>{E(w["week_label"])}</b></span><h1>{E(w["title"])}</h1><p class="hello">{E(w["intro"])}</p></section>
<section class="card"><div class="sec-title"><span class="em">🗓️</span>本周最重要的 {len(w["top"])} 件事</div><ol class="wlist">{tops}</ol></section>
{extra}
<div class="end"><p>每条都链到当天的日报，里面有原文链接和核验记录。</p></div>
</main>
"""
        html_out = (B.head(f'{w["title"]} · 非常AI每周回顾', w["intro"][:80], f'https://feichangai.vip/weekly/{w["date"]}.html', "../")
                    + B.topbar("../", "../" + news_href, "library") + body + B.bottom("../", "../" + news_href) + "</body></html>\n")
        (B.ROOT / "weekly" / f'{w["date"]}.html').write_text(html_out, encoding="utf-8")
    cards = "".join(f"""<article class="ncard" data-cat="周"><div class="nmeta"><span>{E(w["week_label"])}</span></div>
<h3><a href="weekly/{E(w["date"])}.html">{E(w["title"])}</a></h3><p>{E(w["intro"])}</p></article>""" for w in ws)
    if not ws:
        cards = '<p class="lib-note" style="text-align:center;padding:30px 0">第一期每周回顾将在本周日发布 👋</p>'
    lib_page("weekly", "每周回顾", "🗓️", "没空天天看？每周日把这一周最重要的几件事串起来讲清楚。", f"共 {len(ws)} 期",
             f'<div class="nlist">{cards}</div>', "非常AI每周回顾：每周日梳理一周最重要的AI新闻。")
    return len(ws)


# ---------- 资料库总入口 ----------

def build_library(counts):
    def card(href, emo, title, desc, count, colors):
        tiles = "".join(f'<span style="background:{c}">{e}</span>' for c, e in colors)
        return f"""<a class="hub" href="{href}"><div class="tiles">{tiles}</div>
<div class="hub-b"><h3>{emo} {E(title)}</h3><p>{E(desc)}</p><span class="hub-c">{E(count)}</span></div></a>"""
    v, c, m, s = "var(--violet-bg)", "var(--coral-bg)", "var(--mint-bg)", "var(--sun-bg)"
    body = '<div class="hubs">' + "".join([
        card("prompts.html", "🧪", "提示词库", "拿来就能用的提示词，一键复制", f"{counts['prompts']} 条", [(v, "📋"), (c, "🏠"), (m, "🌱"), (s, "✍️")]),
        card("tools.html", "🧰", "AI 工具箱", "每天推荐的新工具，收费和系统写清楚", f"{counts['tools']} 个", [(c, "💻"), (v, "🤖"), (s, "🎨"), (m, "🔒")]),
        card("repos.html", "🐙", "GitHub 开源精选", "靠谱的 Skill、MCP 和 AI 开源项目", f"{counts['repos']} 个", [(v, "🐙"), (m, "🧩"), (s, "⭐"), (c, "🔌")]),
        card("topics.html", "🔎", "新闻话题与搜索", "按公司、话题找往期新闻", f"{counts['topics']} 条新闻", [(m, "🟢"), (v, "🟣"), (c, "🇨🇳"), (s, "#")]),
        card("glossary.html", "📖", "AI 小词典", "看不懂的 AI 词，大白话讲清", f"{counts['glossary']} 个词", [(s, "🔤"), (v, "🧠"), (m, "📦"), (c, "💬")]),
        card("prices.html", "💰", "大模型价格表", "主流模型 API 价格，附官方来源", f"{counts['prices']} 个模型", [(m, "$"), (c, "¥"), (v, "📊"), (s, "⚖️")]),
        card("weekly.html", "🗓️", "每周回顾", "每周日梳理一周大事", f"{counts['weekly']} 期", [(v, "🗓️"), (s, "⭐"), (c, "📰"), (m, "✅")]),
        card("start.html", "👋", "AI 新手入门", "第一次用 AI 从这里看起", "3 分钟读完", [(c, "👋"), (m, "💡"), (v, "💬"), (s, "⚠️")]),
    ]) + "</div>"
    news_href = f"news/{B.latest_date()}.html"
    main = f"""<main class="wrap">
<section class="lib-head"><h1>📚 资料库</h1><p>每天的日报看完就过去了，好东西都攒在这里：提示词、工具、术语、往期新闻、价格表，随时回来查。</p></section>
{body}
</main>
"""
    html_out = (B.head("资料库 · 非常AI", "非常AI资料库：提示词库、AI工具箱、新闻搜索、AI小词典、模型价格表、每周回顾、新手入门。",
                       "https://feichangai.vip/library.html", "")
                + B.topbar("", news_href, "library") + main + B.bottom("", news_href) + "</body></html>\n")
    (B.ROOT / "library.html").write_text(html_out, encoding="utf-8")


def build_all():
    all_issues = issues()
    counts = {
        "prompts": build_prompts(all_issues),
        "tools": build_tools(all_issues),
        "repos": build_repos(all_issues),
        "glossary": build_glossary(all_issues),
        "topics": build_topics(all_issues),
        "weekly": build_weekly_pages(),
        "prices": len(json.loads((B.ROOT / "data" / "prices.json").read_text(encoding="utf-8"))["rows"]),
    }
    build_prices()
    build_start()
    build_library(counts)
    return counts
