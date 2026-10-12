"""
evidence_store · TokenAPI Scan 数据治理 Pillar 3 落盘 SDK

职责
-----
- 把任意原始抓取/探测/采集的字节流(JSON/HTML/响应包)存成内容寻址快照
  (content-addressed snapshot,sha256 文件名),保证幂等。
- 返回 evidence_ref 字符串供 SoR 表(model_canonical/model_alias/price/detection 等)
  的 evidence_ref 字段引用。
- 写入 evidence/<YYYY>/<MM>/<DD>/<sha256>.<ext> 三级日期目录,防单目录炸文件数。

设计原则
--------
1. **幂等**:同样内容写入只产生一个文件,evidence_ref 完全可重现。
2. **不丢原文**:不做压缩/裁剪/打码——原始什么样就什么样(打码是写入端的责任,SDK 不管)。
3. **可审计**:返回 (evidence_ref, sha256, abs_path, bytes) 五元组,调用方可写入审计表。
4. **零依赖**:只用 stdlib;轻到 src/ 任何模块都能 import。

不做什么
--------
- 不连数据库;调用方拿 evidence_ref 自己写 SoR。
- 不验证内容合法性;垃圾进垃圾出。
- 不删除——保留 + 后期 GC 是 governance pipeline 的事。
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_ROOT = Path(os.environ.get(
    "TOKENAPI_EVIDENCE_ROOT",
    Path(__file__).resolve().parents[2] / "web_data" / "evidence",
))


class EvidenceStore:
    """Content-addressed evidence store. Use module-level `put()` for one-shot writes."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root) if root else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    # ---- public ---------------------------------------------------------

    def put(self, payload: bytes | str, ext: str = "json",
            when: Optional[datetime] = None) -> Tuple[str, str, Path, int]:
        """
        Persist a payload. Returns (evidence_ref, sha256, abs_path, bytes_written).

        evidence_ref format:  evidence://YYYY/MM/DD/<sha256>.<ext>
        - URI scheme makes intent unambiguous in DB rows
        - relative path under self.root for portability
        """
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        if not isinstance(data, bytes):
            raise TypeError(f"payload must be bytes or str, got {type(data)!r}")
        sha = hashlib.sha256(data).hexdigest()
        when = when or datetime.now(timezone.utc)
        sub = self.root / when.strftime("%Y") / when.strftime("%m") / when.strftime("%d")
        sub.mkdir(parents=True, exist_ok=True)
        ext = ext.lstrip(".") or "bin"
        abs_path = sub / f"{sha}.{ext}"
        if not abs_path.exists():
            tmp = abs_path.with_suffix(abs_path.suffix + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, abs_path)  # atomic on POSIX same-FS
            bytes_written = len(data)
        else:
            bytes_written = 0  # idempotent no-op; same content already present
        rel = abs_path.relative_to(self.root).as_posix()
        return f"evidence://{rel}", sha, abs_path, bytes_written

    def resolve(self, evidence_ref: str) -> Path:
        """Translate 'evidence://...' back to absolute path. Raise FileNotFoundError if gone."""
        if not evidence_ref.startswith("evidence://"):
            raise ValueError(f"not an evidence ref: {evidence_ref!r}")
        rel = evidence_ref[len("evidence://"):]
        p = self.root / rel
        if not p.exists():
            raise FileNotFoundError(p)
        return p

    def stat(self) -> dict:
        """Counters for ops dashboards (cheap; walks all files once)."""
        n, total = 0, 0
        for p in self.root.rglob("*"):
            if p.is_file() and not p.name.endswith(".tmp"):
                n += 1
                total += p.stat().st_size
        return {"root": str(self.root), "files": n, "bytes": total}


# ---- module-level shorthand -----------------------------------------------

_default: Optional[EvidenceStore] = None


def _store() -> EvidenceStore:
    global _default
    if _default is None:
        _default = EvidenceStore()
    return _default


def put(payload: bytes | str, ext: str = "json",
        when: Optional[datetime] = None) -> Tuple[str, str, Path, int]:
    return _store().put(payload, ext=ext, when=when)


def resolve(evidence_ref: str) -> Path:
    return _store().resolve(evidence_ref)


def stat() -> dict:
    return _store().stat()
