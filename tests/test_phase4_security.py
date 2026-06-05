import gzip
import hashlib
import importlib.util
import pickle
from pathlib import Path
from types import SimpleNamespace

from analyzer.caching.ast_cache import ASTCache


class _PickleExploit:
    def __init__(self, marker_path: Path):
        self.marker_path = marker_path

    def __reduce__(self):
        return (Path(self.marker_path).write_text, ("pickle executed",))


def test_ast_cache_does_not_load_legacy_pickle_payload(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    marker = tmp_path / "owned.txt"

    with gzip.open(cache_dir / "malicious.cache", "wb") as fh:
        pickle.dump(_PickleExploit(marker), fh)

    cache = ASTCache(cache_dir=str(cache_dir), enable_persistence=True)

    assert cache.memory_cache == {}
    assert not marker.exists()
    assert not (cache_dir / "malicious.cache").exists()


def test_ast_cache_persisted_key_uses_sha256_not_md5(tmp_path):
    cache_dir = tmp_path / "cache"
    source = tmp_path / "module.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    cache = ASTCache(cache_dir=str(cache_dir), enable_persistence=True)
    cache.put_analysis_result(source, {"score": 1.0})

    key_material = f"{source.absolute()}:analysis_connascence".encode()
    sha256_key = hashlib.sha256(key_material).hexdigest()
    md5_key = hashlib.md5(key_material).hexdigest()

    assert len(sha256_key) == 64
    assert (cache_dir / f"{sha256_key}.json").exists()
    assert not (cache_dir / f"{md5_key}.json").exists()


def _load_enable_security_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "enable_security.py"
    spec = importlib.util.spec_from_file_location("enable_security", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_enable_security_run_command_never_uses_shell(monkeypatch):
    enable_security = _load_enable_security_module()
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(enable_security.subprocess, "run", fake_run)

    command = ["gh", "api", "repos/example", "--field", "name=ok; echo owned"]
    result = enable_security.run_command(command)

    assert result.returncode == 0
    assert calls == [
        (
            command,
            {
                "shell": False,
                "capture_output": True,
                "text": True,
                "check": False,
            },
        )
    ]


def test_enable_security_rejects_shell_string_commands():
    enable_security = _load_enable_security_module()

    try:
        enable_security.run_command("gh api repos/example; echo owned")
    except TypeError as exc:
        assert "argv sequence" in str(exc)
    else:
        raise AssertionError("shell string command was accepted")
