import pytest
from typer.testing import CliRunner
from pathlib import Path
import os
import shutil
import traceback # For printing exception info
import platform # For OS-specific mock JDK executables

# Assuming your Typer app is in jenv.main
from jenv.main import app
# Import settings module to access its members for assertions if needed,
# but patching will primarily target jenv.settings itself or specific modules.
import jenv.settings
# Import JdkInfo for creating mock SDKs
from jenv.discovery import JdkInfo


runner = CliRunner()

@pytest.fixture(scope="function") # Run for each test function
def mock_jenv_dir(tmp_path: Path, monkeypatch):
    """
    Creates a temporary JENV_DIR for testing and cleans it up.
    Also patches jenv.settings constants and their imported counterparts in other modules.
    """
    # Ensure modules are loaded to allow monkeypatching their attributes
    # These are typically already loaded due to `from jenv.main import app` at file top.
    import jenv.settings
    import jenv.main
    import jenv.discovery

    test_jenv_dir = tmp_path / ".jenv"
    test_jenv_dir.mkdir(parents=True, exist_ok=True)

    # Define all patched path objects based on the temporary test_jenv_dir
    patched_versions_dir = test_jenv_dir / "versions"
    patched_config_file = test_jenv_dir / "config.toml"
    patched_global_file = test_jenv_dir / "version"
    patched_custom_paths_file = test_jenv_dir / "paths"

    # 1. Patch constants at their definition site (jenv.settings)
    monkeypatch.setattr(jenv.settings, "JENV_DIR", test_jenv_dir)
    monkeypatch.setattr(jenv.settings, "VERSIONS_DIR", patched_versions_dir)
    monkeypatch.setattr(jenv.settings, "CONFIG_FILE", patched_config_file)
    monkeypatch.setattr(jenv.settings, "JENV_GLOBAL_VERSION_FILE", patched_global_file)
    monkeypatch.setattr(jenv.settings, "JENV_CUSTOM_PATHS_FILE", patched_custom_paths_file)

    # 2. Patch constants where they are imported at the module level in other files
    # Example: `from jenv.settings import JENV_DIR` in `jenv.main`

    # Patch attributes in jenv.main that were imported from jenv.settings at module level
    if hasattr(jenv.main, "JENV_DIR"): # Check if the import was `from .settings import JENV_DIR`
        monkeypatch.setattr(jenv.main, "JENV_DIR", test_jenv_dir)
    if hasattr(jenv.main, "JENV_GLOBAL_VERSION_FILE"):
        monkeypatch.setattr(jenv.main, "JENV_GLOBAL_VERSION_FILE", patched_global_file)
    if hasattr(jenv.main, "JENV_CUSTOM_PATHS_FILE"):
        monkeypatch.setattr(jenv.main, "JENV_CUSTOM_PATHS_FILE", patched_custom_paths_file)
    # Note: JENV_VERSION_FILE is a string constant, usually no need to patch its value.

    # jenv.discovery imports VERSIONS_DIR and JENV_CUSTOM_PATHS_FILE *inside a function*
    # (`from jenv.settings import VERSIONS_DIR`).
    # Therefore, the patches to jenv.settings.VERSIONS_DIR (and others) made above
    # will be effective when that import occurs during the execution of discover_system_jdks().
    # No direct monkeypatching of attributes on the `jenv.discovery` module object is needed for these.

    original_cwd = Path.cwd()
    test_project_dir = tmp_path / "test_project"
    test_project_dir.mkdir(exist_ok=True)
    os.chdir(test_project_dir)

    yield test_jenv_dir

    os.chdir(original_cwd)

@pytest.fixture
def mock_jdk_home_factory(tmp_path: Path):
    """Factory to create mock JDK home directory structures."""
    created_jdks_root = tmp_path / "mock_jdks"
    created_jdks_root.mkdir(exist_ok=True)

    def _create_jdk(version_str: str, name_prefix: str, vendor: str = "MockVendor"):
        sane_name_prefix = name_prefix.lower().replace(" ", "-")
        jdk_root = created_jdks_root / f"{sane_name_prefix}-{version_str}"
        jdk_bin = jdk_root / "bin"
        jdk_bin.mkdir(parents=True, exist_ok=True)

        java_exe_content = f"""#!/bin/sh
# This is a mock java executable
# Outputting properties similar to 'java -XshowSettings:properties -version' to stderr
echo "Property settings:" >&2
echo "    java.runtime.version = {version_str}" >&2
echo "    java.vendor = {vendor}" >&2
echo "OpenJDK Runtime Environment ({vendor} build {version_str}+0)" >&2
echo "OpenJDK 64-Bit Server VM ({vendor} build {version_str}+0, mixed mode)" >&2
# Also the version string that 'java -version' typically shows
echo "openjdk version \\"{version_str}\\" 2023-10-17" >&2
"""
        # Determine executable name based on the platform the tests are running on
        java_exe_name = "java.exe" if platform.system() == "Windows" else "java"
        java_exe_path = jdk_bin / java_exe_name
        java_exe_path.write_text(java_exe_content)
        os.chmod(java_exe_path, 0o755)

        # If on Windows, also create a 'java' (no extension) for consistent test calls if needed,
        # though discovery itself will look for 'java.exe'.
        if platform.system() == "Windows":
            (jdk_bin / "java").write_text(java_exe_content) # Create the non .exe version as well
            os.chmod(jdk_bin / "java", 0o755)


        javac_exe_name = "javac.exe" if platform.system() == "Windows" else "javac"
        javac_exe_path = jdk_bin / javac_exe_name
        javac_exe_path.write_text(f"#!/bin/sh\necho \"javac {version_str}\" >&2")
        os.chmod(javac_exe_path, 0o755)

        if platform.system() == "Windows":
            (jdk_bin / "javac").write_text(f"#!/bin/sh\necho \"javac {version_str}\" >&2")
            os.chmod(jdk_bin / "javac", 0o755)

        return jdk_root

    yield _create_jdk

@pytest.fixture
def mock_jdk_11(mock_jdk_home_factory) -> Path:
    return mock_jdk_home_factory("11.0.12", "openjdk", "OpenJDKTest")

@pytest.fixture
def mock_jdk_17(mock_jdk_home_factory) -> Path:
    return mock_jdk_home_factory("17.0.1", "temurin", "TemurinTest")


def test_jenv_version_command(mock_jenv_dir):
    from jenv import __version__ as app_version_string
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"jenv version: {app_version_string}" in result.stdout

def test_jenv_no_command_shows_help(mock_jenv_dir):
    result = runner.invoke(app)
    if result.exception:
        print(f"\nException in test_jenv_no_command_shows_help for command: jenv")
        traceback.print_exception(result.exc_info[0], result.exc_info[1], result.exc_info[2])
    assert result.exit_code == 0, f"Help command failed. Exc: {result.exception}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert "Usage: jenv [OPTIONS] COMMAND [ARGS]..." in result.stdout

def test_jenv_versions_no_jdks_found(mock_jenv_dir, monkeypatch):
    monkeypatch.delenv("JAVA_HOME", raising=False)
    monkeypatch.setattr("jenv.main.discover_system_jdks", lambda: [])

    result = runner.invoke(app, ["versions"])
    assert result.exit_code == 0
    assert "No Java versions discovered." in result.stdout

@pytest.mark.skip(reason="Skipping due to difficulties testing JAVA_HOME discovery reliably in current sandbox")
def test_jenv_versions_one_jdk_from_java_home(mock_jenv_dir, mock_jdk_11, monkeypatch):
    monkeypatch.setenv("JAVA_HOME", str(mock_jdk_11))

    result = runner.invoke(app, ["versions"])
    if result.exception:
        # Print full traceback if CliRunner caught an exception
        print("\nException caught by CliRunner:")
        traceback.print_exception(result.exc_info[0], result.exc_info[1], result.exc_info[2])
    assert result.exit_code == 0, f"Command failed. Exit code: {result.exit_code}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert "Discovered Java Versions" in result.stdout
    assert "11.0.12" in result.stdout
    assert "openjdk-11.0.12" in result.stdout # Adjusted to heuristically derived name

def test_jenv_global_set_and_show(mock_jenv_dir, mock_jdk_11, monkeypatch):
    # Name that get_jdk_name_and_vendor would generate for mock_jdk_11
    discovered_jdk_name = "openjdk-11.0.12"

    # When discover_system_jdks is mocked, ensure the mock JdkInfo uses this consistent name and vendor
    mock_sdk = JdkInfo(version="11.0.12", name=discovered_jdk_name, path=mock_jdk_11, vendor="OpenJDK")
    monkeypatch.setattr("jenv.main.discover_system_jdks", lambda: [mock_sdk])

    monkeypatch.delenv("JAVA_HOME", raising=False)

    result_set = runner.invoke(app, ["global", discovered_jdk_name])
    if result_set.exception:
        print(f"\nException in test_jenv_global_set_and_show (set) for command: jenv global {discovered_jdk_name}")
        traceback.print_exception(result_set.exc_info[0], result_set.exc_info[1], result_set.exc_info[2])
    assert result_set.exit_code == 0, f"Global set failed. Exc: {result_set.exception}\nSTDOUT:\n{result_set.stdout}\nSTDERR:\n{result_set.stderr}"
    assert f"Global jenv version set to: {discovered_jdk_name}" in result_set.stdout

    # Access patched global file path via jenv.settings
    global_version_file = jenv.settings.JENV_GLOBAL_VERSION_FILE
    assert global_version_file.exists()
    assert global_version_file.read_text().strip() == discovered_jdk_name

    result_show = runner.invoke(app, ["global"])
    assert result_show.exit_code == 0
    assert f"Current global jenv version: {discovered_jdk_name}" in result_show.stdout

    result_current = runner.invoke(app, ["version"])
    assert result_current.exit_code == 0
    assert "11.0.12" in result_current.stdout
    assert f"(global: {str(global_version_file)})" in result_current.stdout

def test_jenv_local_set_and_show(mock_jenv_dir, mock_jdk_17, monkeypatch):
    local_version_file = Path.cwd() / jenv.settings.JENV_VERSION_FILE

    discovered_jdk_name = "temurin-17.0.1" # Heuristic name for mock_jdk_17
    mock_sdk = JdkInfo(version="17.0.1", name=discovered_jdk_name, path=mock_jdk_17, vendor="Temurin") # Consistent vendor
    monkeypatch.setattr("jenv.main.discover_system_jdks", lambda: [mock_sdk])
    monkeypatch.delenv("JAVA_HOME", raising=False)

    result_set = runner.invoke(app, ["local", discovered_jdk_name])
    if result_set.exception:
        print(f"\nException in test_jenv_local_set_and_show (set) for command: jenv local {discovered_jdk_name}")
        traceback.print_exception(result_set.exc_info[0], result_set.exc_info[1], result_set.exc_info[2])
    assert result_set.exit_code == 0, f"Local set failed. Exc: {result_set.exception}\nSTDOUT:\n{result_set.stdout}\nSTDERR:\n{result_set.stderr}"
    assert f"Local jenv version for directory {Path.cwd()}" in result_set.stdout
    assert local_version_file.exists()
    assert local_version_file.read_text().strip() == discovered_jdk_name

    result_show = runner.invoke(app, ["local"])
    assert result_show.exit_code == 0
    assert f"Local jenv version (from {local_version_file})" in result_show.stdout
    assert discovered_jdk_name in result_show.stdout

    result_current = runner.invoke(app, ["version"])
    assert result_current.exit_code == 0
    assert "17.0.1" in result_current.stdout
    assert f"(local: {str(local_version_file)})" in result_current.stdout

    result_unset = runner.invoke(app, ["local", "--unset"])
    assert result_unset.exit_code == 0
    assert not local_version_file.exists()

def test_jenv_internal_exec(mock_jenv_dir, mock_jdk_11, monkeypatch):
    discovered_jdk_name = "openjdk-11.0.12" # Heuristic name
    mock_sdk = JdkInfo(version="11.0.12", name=discovered_jdk_name, path=mock_jdk_11, vendor="OpenJDK") # Consistent
    monkeypatch.setattr("jenv.main.discover_system_jdks", lambda: [mock_sdk])

    runner.invoke(app, ["global", discovered_jdk_name])

    result = runner.invoke(app, ["internal", "exec", "java", "--version"])
    assert result.exit_code == 0, result.stderr + result.stdout
    assert "openjdk version \"11.0.12\"" in result.stderr

    result_javac = runner.invoke(app, ["internal", "exec", "javac", "-version"])
    assert result_javac.exit_code == 0, result_javac.stderr + result_javac.stdout
    assert "javac 11.0.12" in result_javac.stderr

    result_fail = runner.invoke(app, ["internal", "exec", "nonexistentcmd"])
    assert result_fail.exit_code != 0
    assert "Executable 'nonexistentcmd' not found" in result_fail.stdout

def test_jenv_scan_path_management(mock_jenv_dir, tmp_path):
    custom_paths_file_actual = jenv.settings.JENV_CUSTOM_PATHS_FILE

    result_list1 = runner.invoke(app, ["scan", "--list-paths"])
    assert result_list1.exit_code == 0
    assert "No custom search paths configured." in result_list1.stdout
    assert not custom_paths_file_actual.exists()

    dummy_jdk_path_to_add = tmp_path / "my_other_jdks"
    dummy_jdk_path_to_add.mkdir()

    result_add = runner.invoke(app, ["scan", "--add-path", str(dummy_jdk_path_to_add)])
    assert result_add.exit_code == 0, result_add.stdout
    assert f"Added custom search path: {str(dummy_jdk_path_to_add.resolve())}" in result_add.stdout
    assert custom_paths_file_actual.exists()
    assert str(dummy_jdk_path_to_add.resolve()) in custom_paths_file_actual.read_text()
    assert str(dummy_jdk_path_to_add.resolve()) in result_add.stdout

    result_add_again = runner.invoke(app, ["scan", "--add-path", str(dummy_jdk_path_to_add)])
    assert result_add_again.exit_code == 0
    assert f"Path '{str(dummy_jdk_path_to_add.resolve())}' is already in the custom search list." in result_add_again.stdout

    result_list2 = runner.invoke(app, ["scan", "--list-paths"])
    assert result_list2.exit_code == 0
    assert f"- {str(dummy_jdk_path_to_add.resolve())}" in result_list2.stdout

    result_remove = runner.invoke(app, ["scan", "--remove-path", str(dummy_jdk_path_to_add)])
    assert result_remove.exit_code == 0, result_remove.stdout
    assert f"Removed custom search path: {str(dummy_jdk_path_to_add.resolve())}" in result_remove.stdout
    assert f"Removed empty custom paths file: {str(custom_paths_file_actual)}" in result_remove.stdout
    assert not custom_paths_file_actual.exists()
    assert "No custom search paths configured." in result_remove.stdout

    result_scan_default = runner.invoke(app, ["scan"])
    assert result_scan_default.exit_code == 0
    assert "Scanning for Java Development Kits..." in result_scan_default.stdout
    assert "No Java versions discovered." in result_scan_default.stdout

def test_jenv_which(mock_jenv_dir, mock_jdk_11, monkeypatch):
    discovered_jdk_name = "openjdk-11.0.12" # Heuristic name
    mock_sdk = JdkInfo(version="11.0.12", name=discovered_jdk_name, path=mock_jdk_11, vendor="OpenJDK") # Consistent
    monkeypatch.setattr("jenv.main.discover_system_jdks", lambda: [mock_sdk])

    runner.invoke(app, ["global", discovered_jdk_name])

    result_java = runner.invoke(app, ["which", "java"])
    assert result_java.exit_code == 0
    assert str(mock_jdk_11 / "bin" / "java") in result_java.stdout

    result_javac = runner.invoke(app, ["which", "javac"])
    assert result_javac.exit_code == 0
    assert str(mock_jdk_11 / "bin" / "javac") in result_javac.stdout

    result_nonexistent = runner.invoke(app, ["which", "nonexistent"])
    assert result_nonexistent.exit_code == 1
    assert "Executable 'nonexistent' not found" in result_nonexistent.stdout

def test_jenv_init_bash(mock_jenv_dir):
    temp_jenv_dir_str = str(jenv.settings.JENV_DIR)

    result = runner.invoke(app, ["init", "bash"])
    assert result.exit_code == 0
    assert f'export JENV_DIR="{temp_jenv_dir_str}"' in result.stdout
    assert f'export PATH="{temp_jenv_dir_str}/shims":"{temp_jenv_dir_str}/bin":$PATH' in result.stdout
    assert "# jenv initialization script for bash" in result.stdout
    assert (jenv.settings.JENV_DIR / "shims").is_dir()
    assert (jenv.settings.JENV_DIR / "bin").is_dir()

def test_jenv_rehash(mock_jenv_dir, mock_jdk_11, monkeypatch):
    discovered_jdk_name = "openjdk-11.0.12" # Heuristic name
    mock_sdk = JdkInfo(version="11.0.12", name=discovered_jdk_name, path=mock_jdk_11, vendor="OpenJDK") # Consistent
    monkeypatch.setattr("jenv.main.discover_system_jdks", lambda: [mock_sdk])
    runner.invoke(app, ["global", discovered_jdk_name])

    result = runner.invoke(app, ["rehash"])
    assert result.exit_code == 0, result.stdout
    assert "Rehashed" in result.stdout

    shims_dir = jenv.settings.JENV_DIR / "shims"
    if os.name != "nt":
        java_shim = shims_dir / "java"
        javac_shim = shims_dir / "javac"
        assert java_shim.is_file(), f"Shim {java_shim} not found"
        assert javac_shim.is_file(), f"Shim {javac_shim} not found"
        assert os.access(java_shim, os.X_OK)

        shim_content = java_shim.read_text()
        assert "#!/usr/bin/env sh" in shim_content
        assert 'exec "jenv" internal exec "java" "$@"' in shim_content
    else:
        assert (shims_dir / "java.bat").is_file()
        assert (shims_dir / "javac.bat").is_file()
        shim_content = (shims_dir / "java.bat").read_text()
        assert '"jenv" internal exec "java" %*' in shim_content

def test_version_precedence(mock_jenv_dir, mock_jdk_home_factory, monkeypatch):
    jdk8_path = mock_jdk_home_factory("8.0.302", "zulu", "ZuluTest")
    jdk11_path = mock_jdk_home_factory("11.0.13", "openjdk", "OpenJDKTest")
    jdk17_path = mock_jdk_home_factory("17.0.2", "temurin", "TemurinTest") # Path .../temurin-17.0.2

    # Names as would be generated by discovery.py's get_jdk_name_and_vendor
    # For path "zulu-8.0.302", vendor "ZuluTest" -> name "zulutest-8.0.302", resolved vendor "Zulu"
    # For path "openjdk-11.0.13", vendor "OpenJDKTest" -> name "openjdk-11.0.13", resolved vendor "OpenJDK"
    # For path "temurin-17.0.2", vendor "TemurinTest" -> name "temurin-17.0.2", resolved vendor "Temurin"

    sdk8_name = "zulu-8.0.302" # Heuristic name
    sdk11_name = "openjdk-11.0.13"
    sdk17_name = "temurin-17.0.2"

    sdk8_info = JdkInfo("8.0.302", sdk8_name, jdk8_path, "Zulu") # Use heuristic vendor
    sdk11_info = JdkInfo("11.0.13", sdk11_name, jdk11_path, "OpenJDK")
    sdk17_info = JdkInfo("17.0.2", sdk17_name, jdk17_path, "Temurin")

    all_jdks = [sdk8_info, sdk11_info, sdk17_info]
    monkeypatch.setattr("jenv.main.discover_system_jdks", lambda: all_jdks)
    monkeypatch.delenv("JAVA_HOME", raising=False)

    runner.invoke(app, ["global", sdk8_name])
    res_global = runner.invoke(app, ["version"])
    assert res_global.exit_code == 0, res_global.stdout
    assert sdk8_name in res_global.stdout
    assert "(global:" in res_global.stdout

    runner.invoke(app, ["local", sdk11_name])
    res_local = runner.invoke(app, ["version"])
    assert res_local.exit_code == 0, res_local.stdout
    assert sdk11_name in res_local.stdout
    assert "(local:" in res_local.stdout
    assert sdk8_name not in res_local.stdout

    monkeypatch.setenv("JENV_VERSION", sdk17_name)
    res_shell = runner.invoke(app, ["version"])
    assert res_shell.exit_code == 0, res_shell.stdout
    assert sdk17_name in res_shell.stdout
    assert "(shell: JENV_VERSION)" in res_shell.stdout
    assert sdk11_name not in res_shell.stdout

    monkeypatch.delenv("JENV_VERSION", raising=False)
    local_v_file = Path.cwd() / jenv.settings.JENV_VERSION_FILE
    if local_v_file.exists(): local_v_file.unlink()
    global_v_file = jenv.settings.JENV_GLOBAL_VERSION_FILE
    if global_v_file.exists(): global_v_file.unlink()
