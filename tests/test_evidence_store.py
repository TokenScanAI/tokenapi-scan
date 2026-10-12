"""Test evidence_store SDK (Pillar 3 落盘工具)。"""
import json
import tempfile
from pathlib import Path

import pytest

from governance.evidence_store import EvidenceStore


def test_put_str_and_resolve():
    with tempfile.TemporaryDirectory() as td:
        store = EvidenceStore(root=Path(td))
        ref, sha, path, n = store.put('{"k":"v"}', ext="json")
        assert ref.startswith("evidence://")
        assert ref.endswith(".json")
        assert len(sha) == 64
        assert path.exists()
        assert path.read_text() == '{"k":"v"}'
        assert n == 9
        # resolve roundtrip
        assert store.resolve(ref) == path


def test_put_bytes_idempotent():
    with tempfile.TemporaryDirectory() as td:
        store = EvidenceStore(root=Path(td))
        payload = b"hello world"
        ref1, sha1, path1, n1 = store.put(payload, ext="bin")
        ref2, sha2, path2, n2 = store.put(payload, ext="bin")
        assert ref1 == ref2
        assert sha1 == sha2
        assert path1 == path2
        assert n1 == len(payload)
        assert n2 == 0  # second write was no-op


def test_put_different_content_different_ref():
    with tempfile.TemporaryDirectory() as td:
        store = EvidenceStore(root=Path(td))
        ref_a, _, _, _ = store.put("aaa")
        ref_b, _, _, _ = store.put("bbb")
        assert ref_a != ref_b


def test_resolve_rejects_non_evidence_ref():
    with tempfile.TemporaryDirectory() as td:
        store = EvidenceStore(root=Path(td))
        with pytest.raises(ValueError):
            store.resolve("file:///etc/passwd")


def test_resolve_missing_raises():
    with tempfile.TemporaryDirectory() as td:
        store = EvidenceStore(root=Path(td))
        with pytest.raises(FileNotFoundError):
            store.resolve("evidence://2099/01/01/" + "0" * 64 + ".json")


def test_put_rejects_invalid_type():
    with tempfile.TemporaryDirectory() as td:
        store = EvidenceStore(root=Path(td))
        with pytest.raises(TypeError):
            store.put(123)  # type: ignore[arg-type]


def test_stat_counts():
    with tempfile.TemporaryDirectory() as td:
        store = EvidenceStore(root=Path(td))
        store.put("a")
        store.put("b")
        store.put("c")
        s = store.stat()
        assert s["files"] == 3
        assert s["bytes"] == 3
