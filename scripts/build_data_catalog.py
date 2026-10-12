#!/usr/bin/env python3
"""
TokenAPI Scan · 数据资产清单自动生成器
- 扫 web_data/db/*.db 所有表 + 视图
- 评估治理字段覆盖度 5 件套
- 输出 docs/standards/DATA_CATALOG.md(每周 cron 跑)
- 输出 web_data/governance/data_catalog_snapshot_<DATE>.json(机器可读)

治理字段 5 件套: source / method / fetched_at / verified_at / evidence_ref
其它治理信号: updated_at / status / verified / confidence / evidence

DATA_GOVERNANCE_FRAMEWORK.md Pillar 1 · 实现
"""

from __future__ import annotations
import argparse, json, re, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_DIR       = PROJECT_ROOT / "web_data" / "db"
OUT_MD       = PROJECT_ROOT / "docs" / "standards" / "DATA_CATALOG.auto.md"
OUT_SNAP_DIR = PROJECT_ROOT / "web_data" / "governance"

# 治理字段 5 件套(Pillar 3 锚定)
FIVE_PIECE = {
    "source":       [r"^source$", r"^data_source$", r"^source_name$"],
    "method":       [r"^method$", r"^fetch_method$", r"^collect_method$"],
    "fetched_at":   [r"^fetched_at$", r"^collected_at$", r"^scraped_at$", r"^seen_at$"],
    "verified_at":  [r"^verified_at$", r"^validated_at$"],
    "evidence_ref": [r"^evidence_ref$", r"^evidence$", r"^raw_response_ref$", r"^snapshot_ref$"],
}

EXTRA = {
    "updated_at":  [r"updated_at$", r"^modified_at$", r"^last_updated$"],
    "status":      [r"^status$", r"^state$"],
    "confidence":  [r"confidence$", r"trust_score$"],
    "verified":    [r"^verified$", r"^is_verified$"],
}

def match_any(col: str, patterns: list[str]) -> bool:
    return any(re.match(p, col) for p in patterns)

def scan_db(db_path: Path) -> dict:
    out = {"db": db_path.name, "tables": [], "views": []}
    try:
        # 关键:不能 mode=ro,否则看不到 WAL 中未 checkpoint 的最新 schema/行数。
        # 用 RW 但只跑 SELECT/PRAGMA(治理脚本约束),实际进程开 WAL 后 readers 会读到最新版本。
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # 强制 WAL checkpoint 一次,确保 PRAGMA table_info 看到最新结构
        try:
            cur.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except sqlite3.Error:
            pass
    except sqlite3.Error as e:
        out["error"] = str(e); return out

    cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type, name")
    objs = cur.fetchall()

    for o in objs:
        name, otype = o["name"], o["type"]
        try:
            cols = [r["name"] for r in cur.execute(f"PRAGMA table_info({name})").fetchall()]
        except sqlite3.Error:
            cols = []
        rows = "?"
        try:
            r = cur.execute(f"SELECT COUNT(*) AS c FROM {name}").fetchone()
            rows = r["c"]
        except sqlite3.Error:
            pass

        five = {k: any(match_any(c, pats) for c in cols) for k, pats in FIVE_PIECE.items()}
        extra = {k: any(match_any(c, pats) for c in cols) for k, pats in EXTRA.items()}
        five_score = sum(five.values())
        extra_score = sum(extra.values())

        # 治理等级 A/B/C/D
        if five_score >= 4 and extra.get("updated_at"):
            level = "A"
        elif five_score >= 3:
            level = "B"
        elif five_score >= 1 or extra.get("updated_at"):
            level = "C"
        else:
            level = "D"

        entry = dict(name=name, type=otype, columns=len(cols), rows=rows,
                     five_piece=five, extra=extra, five_score=five_score,
                     extra_score=extra_score, governance_level=level)
        if otype == "view":
            out["views"].append(entry)
        else:
            out["tables"].append(entry)
    conn.close()
    return out

def render_md(snaps: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# TokenAPI Scan · 数据资产清单（DATA_CATALOG）",
        f"",
        f"自动生成于：{now}（脚本 `scripts/governance/build_data_catalog.py`）",
        f"状态：本文档每周一 09:00 cron 自动刷新；**禁止手写**。",
        f"关联：DATA_GOVERNANCE_FRAMEWORK.md Pillar 1",
        "",
        "## 0. 治理字段说明",
        "",
        "五件套(Pillar 3):`source · method · fetched_at · verified_at · evidence_ref`",
        "扩展信号:`updated_at · status · confidence · verified`",
        "",
        "| Level | 含义 |",
        "|---|---|",
        "| **A** | 五件套 ≥ 4 + updated_at,**入产标杆** |",
        "| **B** | 五件套 ≥ 3,**可用** |",
        "| **C** | 有部分治理字段,**待加固** |",
        "| **D** | 0 个五件套字段,**优先治理** |",
        "",
        "---",
        "",
    ]

    # 汇总
    total_tables = sum(len(s["tables"]) for s in snaps)
    total_views  = sum(len(s["views"])  for s in snaps)
    levels = {"A":0,"B":0,"C":0,"D":0}
    five_sum = 0
    for s in snaps:
        for t in s["tables"]:
            levels[t["governance_level"]] += 1
            five_sum += t["five_score"]
    coverage = (five_sum / (total_tables * 5) * 100) if total_tables else 0

    lines += [
        f"## 1. 汇总",
        "",
        f"- 数据库:{len(snaps)} 个",
        f"- 表:{total_tables}  视图:{total_views}",
        f"- 五件套总覆盖率:**{coverage:.1f}%**",
        f"- 治理等级分布:A={levels['A']} / B={levels['B']} / C={levels['C']} / D={levels['D']}",
        "",
        "**北极星指标:** 12 个月内表 100% 达到 A 级。",
        "",
        "---",
        "",
        "## 2. 各表详细",
        "",
    ]

    for s in snaps:
        if "error" in s:
            lines += [f"### DB `{s['db']}` ⚠ 读取失败:{s['error']}", ""]
            continue
        lines += [f"### DB `{s['db']}`", ""]
        if s["tables"]:
            lines += [
                "| 表 | 行数 | 列数 | source | method | fetched_at | verified_at | evidence_ref | updated_at | 等级 |",
                "|---|---|---|---|---|---|---|---|---|---|",
            ]
            for t in sorted(s["tables"], key=lambda x: (-x["five_score"], x["name"])):
                fp = t["five_piece"]
                ex = t["extra"]
                ch = lambda b: "✅" if b else "—"
                lines.append(
                    f"| `{t['name']}` | {t['rows']} | {t['columns']} | "
                    f"{ch(fp['source'])} | {ch(fp['method'])} | {ch(fp['fetched_at'])} | "
                    f"{ch(fp['verified_at'])} | {ch(fp['evidence_ref'])} | "
                    f"{ch(ex['updated_at'])} | **{t['governance_level']}** |"
                )
            lines.append("")
        if s["views"]:
            vnames = ", ".join("`" + v["name"] + "`" for v in s["views"])
            lines += [f"**视图:** {vnames}", ""]

    lines += [
        "---",
        "",
        "## 3. 优先治理目标(D 级表清单)",
        "",
    ]
    d_tables = []
    for s in snaps:
        for t in s["tables"]:
            if t["governance_level"] == "D":
                d_tables.append((s["db"], t))
    if not d_tables:
        lines.append("无 D 级表 ✅")
    else:
        lines.append("| DB | 表 | 行数 | 推荐动作 |")
        lines.append("|---|---|---|---|")
        for db, t in d_tables:
            action = "Sprint 1 加五件套" if t["rows"] and t["rows"] != 0 else "暂缓(0 行)"
            lines.append(f"| `{db}` | `{t['name']}` | {t['rows']} | {action} |")
    lines.append("")

    lines += [
        "---",
        "",
        "## 4. 标杆表(A/B 级,作为治理模板)",
        "",
    ]
    bench = []
    for s in snaps:
        for t in s["tables"]:
            if t["governance_level"] in ("A","B") and (isinstance(t["rows"], int) and t["rows"] > 0):
                bench.append((s["db"], t))
    if bench:
        lines.append("| DB | 表 | 等级 | 五件套字段 |")
        lines.append("|---|---|---|---|")
        for db, t in bench:
            owned = [k for k, v in t["five_piece"].items() if v]
            lines.append(f"| `{db}` | `{t['name']}` | **{t['governance_level']}** | {', '.join(owned)} |")
    else:
        lines.append("(无 A/B 级表,需要新建标杆)")
    lines.append("")

    lines += [
        "---",
        "",
        "## 5. 操作指引",
        "",
        "- 给一张表加治理字段:见 `DATA_GOVERNANCE_FRAMEWORK.md` Pillar 3",
        "- 走 Gate-IN 写入:见 `DATA_VERIFICATION_STANDARD.md` §2",
        "- 评估表治理等级:跑本脚本 `python3 scripts/governance/build_data_catalog.py`",
        "",
    ]
    return "\n".join(lines) + "\n"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只输出到 stdout 不写文件")
    args = ap.parse_args()

    dbs = sorted(DB_DIR.glob("*.db"))
    if not dbs:
        print(f"[catalog] no DBs in {DB_DIR}", file=sys.stderr); return 1
    snaps = [scan_db(db) for db in dbs]
    md = render_md(snaps)

    if args.dry_run:
        print(md); return 0

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"[catalog] wrote {OUT_MD}")

    OUT_SNAP_DIR.mkdir(parents=True, exist_ok=True)
    snap_path = OUT_SNAP_DIR / f"data_catalog_snapshot_{datetime.now().strftime('%Y%m%d')}.json"
    snap_path.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(), "snapshots": snaps},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[catalog] wrote {snap_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
