"""每日简报复核脚本：检查九章骨架、条数、四层结构、禁用项。"""
import re
import sys


CHAPTERS = [
    ("一、财经热点", re.compile(r"^##\s*一、财经热点")),
    ("二、微博热搜 TOP 10", re.compile(r"^##\s*二、微博热搜")),
    ("三、抖音热搜 TOP 10", re.compile(r"^##\s*三、抖音热搜")),
    ("四、百度热搜 TOP 10", re.compile(r"^##\s*四、百度热搜")),
    ("五、全网交叉热点", re.compile(r"^##\s*五、全网交叉热点")),
    ("六、三处反差", re.compile(r"^##\s*六、三处反差")),
    ("七、待办", re.compile(r"^##\s*七、待办")),
    ("八、日程", re.compile(r"^##\s*八、日程")),
    ("九、明天可以盯的", re.compile(r"^##\s*九、明天可以盯的")),
]
FIELD = re.compile(r"^##\s*(?:[一二三四五六七八九十]、)?([^\n（(]*)")
ITEM = re.compile(r"^\*\*(?:\d+[.、]|[一二三四五六七八九十]+、)")


def split_sections(lines):
    sections = []
    current = None
    for line in lines:
        m = FIELD.match(line.strip())
        if m:
            current = {"title": m.group(1).strip(), "lines": []}
            sections.append(current)
        elif current is not None:
            current["lines"].append(line)
    return sections


def count_items(lines):
    return sum(1 for ln in lines if ITEM.match(ln.strip()))


def main():
    if len(sys.argv) < 2:
        print("用法: python check_brief.py <简报文件路径>")
        return 2
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    problems = []

    positions = []
    for name, pat in CHAPTERS:
        idx = next((i for i, ln in enumerate(lines) if pat.match(ln.strip())), None)
        if idx is None:
            problems.append("缺章节：" + name)
        else:
            positions.append(idx)
    if positions == sorted(positions) and len(positions) == len(CHAPTERS):
        print("[PASS] 九章齐全，顺序正确")
    else:
        print("[FAIL] 章节缺失或顺序错乱")

    by_title = {}
    for s in split_sections(lines):
        by_title.setdefault(s["title"], s)

    fin = by_title.get("财经热点")
    fin_n = count_items(fin["lines"]) if fin else 0
    m = re.search(r"财经热点（(\d+)\s*条）", text)
    declared = int(m.group(1)) if m else None
    if fin_n >= 20:
        print("[PASS] 财经条数 %d 条（>=20）" % fin_n)
    else:
        print("[FAIL] 财经条数 %d 条，少于 20" % fin_n)
        problems.append("财经条数不足")
    if declared is not None:
        if declared == fin_n:
            print("[PASS] 标题声明 %d 条与实际一致" % declared)
        else:
            print("[FAIL] 标题声明 %d 条，实际 %d 条" % (declared, fin_n))
            problems.append("财经条数与标题不一致")

    for key in ("微博热搜 TOP 10", "抖音热搜 TOP 10", "百度热搜 TOP 10"):
        sec = by_title.get(key)
        n = count_items(sec["lines"]) if sec else 0
        if n == 10:
            print("[PASS] %s 10 条" % key)
        else:
            print("[FAIL] %s %d 条，应为 10 条" % (key, n))
            problems.append(key + " 条数不对")

    sec = by_title.get("三处反差")
    n = count_items(sec["lines"]) if sec else 0
    if n == 3:
        print("[PASS] 三处反差 3 条")
    else:
        print("[FAIL] 三处反差 %d 条，应为 3 条" % n)
        problems.append("三处反差条数不对")

    total_items = fin_n + 30
    summary_n = text.count("**小结：**")
    link_n = text.count("直达：")
    if summary_n == total_items:
        print("[PASS] 小结 %d 个 = 条目数 %d" % (summary_n, total_items))
    else:
        print("[FAIL] 小结 %d 个，条目数 %d" % (summary_n, total_items))
        problems.append("小结数与条目数不一致")
    if link_n >= total_items:
        print("[PASS] 直达链接 %d 条（>=%d）" % (link_n, total_items))
    else:
        print("[FAIL] 直达链接 %d 条，少于条目数 %d" % (link_n, total_items))
        problems.append("直达链接不足")

    zhihu = text.count("知乎")
    if zhihu <= 1:
        print("[PASS] 知乎出现 %d 次（<=1）" % zhihu)
    else:
        print("[FAIL] 知乎出现 %d 次，正文混入了知乎内容" % zhihu)
        problems.append("含知乎内容")

    table_rows = [ln for ln in lines if ln.count("|") >= 2]
    if not table_rows:
        print("[PASS] 正文无表格")
    else:
        print("[FAIL] 正文有 %d 行表格结构" % len(table_rows))
        problems.append("正文含表格")

    print("[INFO] 行数 %d，字节数 %d" % (len(lines), len(text.encode("utf-8"))))

    if problems:
        print("[RESULT] FAIL -- " + "；".join(problems))
        return 1
    print("[RESULT] PASS -- 全部检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
