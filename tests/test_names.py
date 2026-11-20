"""OPSIN availability with and without a Java runtime (no database needed)."""

import subprocess

import pytest

from mcp_bindingdb import names

pytestmark = pytest.mark.skipif(names.jpype is None, reason="pyopsin not installed")
bundled_jvm = names._bundled_jvm


@pytest.fixture
def no_jvm(monkeypatch):
    """No JVM running and no jdk4py runtime (test_bundled_java_runtime puts that back)."""
    names.opsin_unavailable_reason.cache_clear()
    monkeypatch.setattr(names.jpype, "isJVMStarted", lambda: False)
    monkeypatch.setattr(names, "_bundled_jvm", lambda: None)
    yield
    names.opsin_unavailable_reason.cache_clear()


def test_java_home_failing(no_jvm, monkeypatch):
    # macOS without a JDK: JPype's /usr/libexec/java_home call exits 1 (CalledProcessError, not
    # JVMNotFoundException); this crashed the server at start-up on such Macs.
    def java_home_fails():
        raise subprocess.CalledProcessError(1, ["/usr/libexec/java_home"])
    monkeypatch.setattr(names, "_no_macos_jdk", lambda: False)
    monkeypatch.setattr(names.jpype, "getDefaultJVMPath", java_home_fails)
    assert names.opsin_unavailable_reason() == "no Java runtime found"


def test_no_macos_jdk_skips_java_home(no_jvm, monkeypatch):
    def must_not_run():
        raise AssertionError("java_home should not run without a JDK")
    monkeypatch.setattr(names, "_no_macos_jdk", lambda: True)
    monkeypatch.setattr(names.jpype, "getDefaultJVMPath", must_not_run)
    assert names.opsin_unavailable_reason() == "no Java runtime found"


def test_no_macos_jdk(monkeypatch, tmp_path):
    monkeypatch.setattr(names.sys, "platform", "darwin")
    monkeypatch.delenv("JAVA_HOME", raising=False)
    monkeypatch.setattr(names.Path, "home", lambda: tmp_path)
    jvms = tmp_path / "Library/Java/JavaVirtualMachines"
    real_root = names.Path("/Library/Java/JavaVirtualMachines")
    if real_root.is_dir() and any(real_root.iterdir()):
        assert not names._no_macos_jdk()  # a system-wide JDK is installed on this computer
    else:
        assert names._no_macos_jdk()
        (jvms / "jdk-21.jdk").mkdir(parents=True)
        assert not names._no_macos_jdk()
    monkeypatch.setenv("JAVA_HOME", "/somewhere")
    assert not names._no_macos_jdk()
    monkeypatch.setattr(names.sys, "platform", "linux")
    monkeypatch.delenv("JAVA_HOME")
    assert not names._no_macos_jdk()


@pytest.mark.skipif(names.jdk4py is None, reason="jdk4py not installed")
def test_bundled_java_runtime(no_jvm, monkeypatch):
    # With jdk4py, OPSIN needs no installed Java: neither java_home nor JAVA_HOME is consulted.
    def must_not_run():
        raise AssertionError("an installed Java should not be looked for")
    monkeypatch.setattr(names.jpype, "getDefaultJVMPath", must_not_run)
    monkeypatch.setattr(names, "_no_macos_jdk", lambda: True)
    monkeypatch.setattr(names, "_bundled_jvm", bundled_jvm)
    assert names._bundled_jvm().is_file()
    assert names.opsin_unavailable_reason() is None
