
import typer
from typing import List, Optional
from pathlib import Path
import os
import platform
import logging
import sys

from rich.console import Console
from rich.table import Table

from jenv import __version__ as jenv_app_version
from jenv.discovery import discover_system_jdks, JdkInfo, get_java_version_from_path, get_jdk_name_and_vendor
from jenv.settings import JENV_VERSION_ENV_VAR, JENV_VERSION_FILE, JENV_GLOBAL_VERSION_FILE, JENV_DIR, JENV_CUSTOM_PATHS_FILE
from jenv.util import read_version_file, write_version_file, get_active_jdk_path_from_env
from jenv.downloader import JdkDownloader, MavenDownloader, DownloadError



app = typer.Typer(name="jenv", help="Java Environment Manager", invoke_without_command=True)
console = Console()
err_console = Console(stderr=True, style="bold red")

logging.basicConfig(
    level=os.environ.get("JENV_LOG_LEVEL", "WARNING").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


def get_currently_active_jdk() -> Optional[JdkInfo]:
    jenv_version_env = os.environ.get(JENV_VERSION_ENV_VAR)
    if jenv_version_env:
        current_java_home = get_active_jdk_path_from_env()
        if current_java_home:
            version = get_java_version_from_path(current_java_home)
            if version:
                discovered_jdks = discover_system_jdks()
                for jdk in discovered_jdks:
                    if jdk.path == current_java_home:
                        if jdk.name == jenv_version_env or str(jdk.path) == jenv_version_env:
                            return JdkInfo(version=jdk.version, name=f"{jdk.name} (shell: JENV_VERSION)", path=jdk.path, vendor=jdk.vendor, is_jenv_managed=jdk.is_jenv_managed)
                name, vendor = get_jdk_name_and_vendor(current_java_home, version)
                return JdkInfo(version=version, name=f"{name} (shell: JENV_VERSION)", path=current_java_home, vendor=vendor)

    current_dir = Path.cwd()
    jenv_version_path = None
    while current_dir != current_dir.parent:
        if (current_dir / JENV_VERSION_FILE).exists():
            jenv_version_path = current_dir / JENV_VERSION_FILE
            break
        current_dir = current_dir.parent
    if (current_dir / JENV_VERSION_FILE).exists():
        jenv_version_path = current_dir / JENV_VERSION_FILE

    if jenv_version_path:
        local_version_name = read_version_file(jenv_version_path)
        if local_version_name:
            discovered_jdks = discover_system_jdks()
            for jdk in discovered_jdks:
                if jdk.name == local_version_name or str(jdk.path) == local_version_name:
                    return JdkInfo(version=jdk.version, name=f"{jdk.name} (local: {jenv_version_path})", path=jdk.path, vendor=jdk.vendor, is_jenv_managed=jdk.is_jenv_managed)

    if JENV_GLOBAL_VERSION_FILE.exists():
        global_version_name = read_version_file(JENV_GLOBAL_VERSION_FILE)
        if global_version_name:
            discovered_jdks = discover_system_jdks()
            for jdk in discovered_jdks:
                if jdk.name == global_version_name or str(jdk.path) == global_version_name:
                    return JdkInfo(version=jdk.version, name=f"{jdk.name} (global: {JENV_GLOBAL_VERSION_FILE})", path=jdk.path, vendor=jdk.vendor, is_jenv_managed=jdk.is_jenv_managed)

    current_java_home = get_active_jdk_path_from_env()
    if current_java_home:
        version = get_java_version_from_path(current_java_home)
        if version:
            name, vendor = get_jdk_name_and_vendor(current_java_home, version)
            discovered_jdks = discover_system_jdks()
            for jdk in discovered_jdks:
                if jdk.path == current_java_home:
                    return JdkInfo(version=jdk.version, name=f"{jdk.name} (JAVA_HOME)", path=jdk.path, vendor=jdk.vendor, is_jenv_managed=jdk.is_jenv_managed)
            return JdkInfo(version=version, name=f"{name} (JAVA_HOME)", path=current_java_home, vendor=vendor)

    return None


@app.command(name="version", help="Show the currently active Java version and how it was set.")
def current_version():
    """
    Shows the currently active Java version.
    """
    active_jdk = get_currently_active_jdk()
    if active_jdk:
        console.print(f"Active JDK: [bold green]{active_jdk.version}[/bold green] (Vendor: {active_jdk.vendor if active_jdk.vendor else 'N/A'})")
        console.print(f"  Name: {active_jdk.name}")
        console.print(f"  Path: {active_jdk.path}")
    else:
        # Try to get system `java -version` directly if no JAVA_HOME is set or jenv managed.
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=2)
            # java -version prints to stderr
            output = result.stderr.strip()
            first_line = output.splitlines()[0] if output.splitlines() else "N/A"
            console.print(f"System Java (not managed by jenv, from PATH): [bold cyan]{first_line}[/bold cyan]")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            err_console.print("No active Java version found (JAVA_HOME not set, jenv not configured, or 'java' not in PATH).")


@app.command(name="versions", help="List all discovered Java versions.")
@app.command(name="list", help="Alias for 'versions'.") # Alias
def list_versions(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full paths and vendor information.")
):
    """
    Lists all Java versions discovered by jenv.
    """
    jdks = discover_system_jdks()
    active_jdk_info = get_currently_active_jdk() # Get info about the truly active one

    if not jdks:
        console.print("No Java versions discovered. Try 'jenv scan' or configure search paths.")
        return

    table = Table(title="Discovered Java Versions")
    table.add_column("Active", style="dim", width=6)
    table.add_column("Version", style="cyan")
    table.add_column("Name", style="magenta")
    if verbose:
        table.add_column("Vendor", style="yellow")
        table.add_column("Path", style="green")
        table.add_column("Managed", style="blue")

    for jdk in jdks:
        is_active_marker = "*" if active_jdk_info and jdk.path == active_jdk_info.path else ""
        if verbose:
            table.add_row(
                is_active_marker,
                jdk.version,
                jdk.name,
                jdk.vendor if jdk.vendor else "N/A",
                str(jdk.path),
                "Yes" if jdk.is_jenv_managed else "No"
            )
        else:
            table.add_row(
                is_active_marker,
                jdk.version,
                jdk.name
            )
    console.print(table)

@app.command(name="global", help="Set or show the global Java version.")
def set_global_version(
    version_name: Optional[str] = typer.Argument(None, help="The name or path of the JDK to set as global. If not provided, shows current global.")
):
    """
    Sets the global Java version for the user.
    This version is used when no local or shell version is set.
    """
    if version_name is None:
        current_global_name = read_version_file(JENV_GLOBAL_VERSION_FILE)
        if current_global_name:
            # Resolve and display more info
            discovered_jdks = discover_system_jdks()
            found_jdk = None
            for jdk in discovered_jdks:
                if jdk.name == current_global_name or str(jdk.path) == current_global_name:
                    found_jdk = jdk
                    break
            if found_jdk:
                console.print(f"Current global jenv version: [bold green]{found_jdk.name}[/bold green] (Version: {found_jdk.version}, Path: {found_jdk.path})")
            else:
                console.print(f"Current global jenv version name: [bold yellow]{current_global_name}[/bold yellow] (JDK not currently discovered).")
        else:
            console.print("No global jenv version is set. Use 'jenv global <version_name_or_path>' to set one.")
        return

    discovered_jdks = discover_system_jdks()
    target_jdk: Optional[JdkInfo] = None

    # Try to match by name first, then by path prefix/exact match if name is a path
    for jdk in discovered_jdks:
        if jdk.name == version_name:
            target_jdk = jdk
            break
    if not target_jdk:
        # Try path matching if version_name looks like a path
        try:
            path_from_arg = Path(version_name).resolve()
            for jdk in discovered_jdks:
                if jdk.path == path_from_arg:
                    target_jdk = jdk
                    break
        except Exception: # Not a valid path or other error
            pass

    # Try partial version matching (e.g., "17" should match "temurin-17.0.5")
    if not target_jdk:
        potential_matches = []
        for jdk in discovered_jdks:
            if version_name in jdk.version or version_name in jdk.name:
                potential_matches.append(jdk)
        if len(potential_matches) == 1:
            target_jdk = potential_matches[0]
        elif len(potential_matches) > 1:
            err_console.print(f"Ambiguous version '{version_name}'. Multiple JDKs found:")
            for match in potential_matches:
                err_console.print(f"  - {match.name} ({match.version}) at {match.path}")
            err_console.print("Please be more specific.")
            raise typer.Exit(code=1)


    if target_jdk:
        write_version_file(JENV_GLOBAL_VERSION_FILE, target_jdk.name) # Store by its jenv-known name
        console.print(f"Global jenv version set to: [bold green]{target_jdk.name}[/bold green] (Version {target_jdk.version})")
        console.print(f"Path: {target_jdk.path}")
        console.print("Note: This sets the jenv global default. You may need to run 'jenv init -' or similar")
        console.print("in your shell profile, or open a new shell, for JAVA_HOME to be updated by jenv's shims/scripts.")
    else:
        err_console.print(f"JDK version '{version_name}' not found among discovered JDKs.")
        err_console.print("Run 'jenv versions' to see available JDKs.")
        raise typer.Exit(code=1)


def _version_callback(value: bool):
    if value:
        console.print(f"jenv version: {jenv_app_version} - Crafted with ❤️ by Cheikh Tidiane")
        raise typer.Exit()

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(None, "--version", callback=_version_callback, is_eager=True, help="Show the application version and exit.")
):
    """
    jenv: A Java Environment Manager.
    Manages multiple Java Development Kit (JDK) installations.
    """
    JENV_DIR.mkdir(parents=True, exist_ok=True) # Ensure base directory exists


@app.command(name="local", help="Set or show the local Java version (for the current directory).")
def set_local_version(
    version_name: Optional[str] = typer.Argument(None, help="The name or path of the JDK to set as local. If not provided, shows current local config."),
    unset: bool = typer.Option(False, "--unset", help="Remove the local .jenv-version file.")
):
    """
    Sets or shows the local Java version by creating or reading a .jenv-version file
    in the current directory. This version overrides the global version.
    """
    local_version_file_path = Path.cwd() / JENV_VERSION_FILE

    if unset:
        if local_version_file_path.exists():
            try:
                local_version_file_path.unlink()
                console.print(f"Local version configuration removed: {local_version_file_path}")
            except OSError as e:
                err_console.print(f"Error removing {local_version_file_path}: {e}")
                raise typer.Exit(code=1)
        else:
            console.print(f"No local version configuration ({JENV_VERSION_FILE}) found in the current directory.")
        return

    if version_name is None:
        # Traverse upwards to find .jenv-version
        current_dir = Path.cwd()
        found_config_path: Optional[Path] = None
        while current_dir != current_dir.parent: # Stop at root
            if (current_dir / JENV_VERSION_FILE).exists():
                found_config_path = current_dir / JENV_VERSION_FILE
                break
            current_dir = current_dir.parent
        if (current_dir / JENV_VERSION_FILE).exists(): # Check root dir as well
             found_config_path = current_dir / JENV_VERSION_FILE

        if found_config_path:
            current_local_name = read_version_file(found_config_path)
            if current_local_name:
                # Resolve and display more info
                discovered_jdks = discover_system_jdks()
                found_jdk = None
                for jdk in discovered_jdks:
                    if jdk.name == current_local_name or str(jdk.path) == current_local_name:
                        found_jdk = jdk
                        break
                if found_jdk:
                    console.print(f"Local jenv version (from {found_config_path}): [bold green]{found_jdk.name}[/bold green] (Version: {found_jdk.version}, Path: {found_jdk.path})")
                else:
                    console.print(f"Local jenv version name (from {found_config_path}): [bold yellow]{current_local_name}[/bold yellow] (JDK not currently discovered).")
            else: # Should not happen if file exists and read_version_file is robust
                err_console.print(f"Local version file {found_config_path} is empty or unreadable.")
        else:
            console.print(f"No local version configuration ({JENV_VERSION_FILE}) found in current or parent directories.")
            console.print("Use 'jenv local <version_name_or_path>' to set one for the current directory.")
        return

    # Setting a new local version
    discovered_jdks = discover_system_jdks()
    target_jdk: Optional[JdkInfo] = None

    # Try to match by name first
    for jdk in discovered_jdks:
        if jdk.name == version_name:
            target_jdk = jdk
            break
    if not target_jdk: # Then by path
        try:
            path_from_arg = Path(version_name).resolve()
            for jdk in discovered_jdks:
                if jdk.path == path_from_arg:
                    target_jdk = jdk
                    break
        except Exception:
            pass

    # Try partial version matching
    if not target_jdk:
        potential_matches = []
        for jdk in discovered_jdks:
            if version_name in jdk.version or version_name in jdk.name:
                potential_matches.append(jdk)
        if len(potential_matches) == 1:
            target_jdk = potential_matches[0]
        elif len(potential_matches) > 1:
            err_console.print(f"Ambiguous version '{version_name}'. Multiple JDKs found:")
            for match in potential_matches:
                err_console.print(f"  - {match.name} ({match.version}) at {match.path}")
            err_console.print("Please be more specific.")
            raise typer.Exit(code=1)

    if target_jdk:
        write_version_file(local_version_file_path, target_jdk.name) # Store by its jenv-known name
        console.print(f"Local jenv version for directory [bold cyan]{Path.cwd()}[/bold cyan] set to: [bold green]{target_jdk.name}[/bold green] (Version {target_jdk.version})")
        console.print(f"Created/updated: {local_version_file_path}")
        console.print("Note: For this to take effect, jenv's shell integration (e.g., 'eval \"$(jenv init -)\"') must be active.")
    else:
        err_console.print(f"JDK version '{version_name}' not found among discovered JDKs.")
        err_console.print("Run 'jenv versions' to see available JDKs.")
        raise typer.Exit(code=1)


@app.command(name="shell", help="Set the Java version for the current shell session (requires shell integration).")
def set_shell_version(
    version_name: Optional[str] = typer.Argument(None, help="The JDK version name/path to activate for this shell session."),
    unset: bool = typer.Option(False, "--unset", help=f"Deactivate shell-specific version, unsetting {JENV_VERSION_ENV_VAR}.")
):
    """
    Sets a shell-specific Java version by (conceptually) setting the JENV_VERSION environment variable.
    Requires 'eval "$(jenv init -)"' in your shell's rc file for full effect.
    """
    if unset:
        console.print(f"To unset the shell version, run in your shell (if using bash/zsh/fish):")
        console.print(f"  unset {JENV_VERSION_ENV_VAR}")
        console.print(f"Or for Windows CMD (requires jenv init support):")
        console.print(f"  set {JENV_VERSION_ENV_VAR}=")
        console.print("\nThis command ('jenv shell --unset') doesn't directly modify the parent shell environment.")
        console.print("It will be effective once 'jenv init -' logic is fully implemented and used.")
        # When jenv init is active, this command could tell the init script to unset the var.
        return

    if version_name is None:
        shell_ver_name = os.environ.get(JENV_VERSION_ENV_VAR)
        if shell_ver_name:
            # Resolve and display more info
            discovered_jdks = discover_system_jdks()
            found_jdk = None
            for jdk in discovered_jdks: # Match by name or path
                if jdk.name == shell_ver_name or str(jdk.path) == shell_ver_name:
                    found_jdk = jdk
                    break
            if found_jdk:
                console.print(f"Current shell jenv version ({JENV_VERSION_ENV_VAR}): [bold green]{found_jdk.name}[/bold green] (Version: {found_jdk.version}, Path: {found_jdk.path})")
            else:
                console.print(f"Current shell jenv version name ({JENV_VERSION_ENV_VAR}): [bold yellow]{shell_ver_name}[/bold yellow] (JDK not currently discovered or name is a direct path).")
        else:
            console.print(f"No shell-specific jenv version is set ({JENV_VERSION_ENV_VAR} is not defined).")
            console.print("Use 'jenv shell <version_name_or_path>' to set one (requires shell integration).")
        return

    discovered_jdks = discover_system_jdks()
    target_jdk: Optional[JdkInfo] = None
    # Match logic (similar to global/local)
    for jdk in discovered_jdks:
        if jdk.name == version_name:
            target_jdk = jdk
            break
    if not target_jdk:
        try:
            path_from_arg = Path(version_name).resolve()
            for jdk in discovered_jdks:
                if jdk.path == path_from_arg:
                    target_jdk = jdk
                    break
        except Exception: pass

    if not target_jdk:
        potential_matches = []
        for jdk in discovered_jdks:
            if version_name in jdk.version or version_name in jdk.name:
                potential_matches.append(jdk)
        if len(potential_matches) == 1: target_jdk = potential_matches[0]
        elif len(potential_matches) > 1:
            err_console.print(f"Ambiguous version '{version_name}'. Multiple JDKs found. Please be more specific.")
            raise typer.Exit(code=1)

    if target_jdk:
        console.print(f"To activate JDK '{target_jdk.name}' (Version {target_jdk.version}) for the current shell:")
        console.print(f"Run the following in your shell (example for bash/zsh/fish):")
        console.print(f"  export {JENV_VERSION_ENV_VAR}=\"{target_jdk.name}\"") # Use name for consistency
        console.print(f"Or for Windows CMD (requires jenv init support for full integration):")
        console.print(f"  set {JENV_VERSION_ENV_VAR}={target_jdk.name}")
        console.print("\nThis command ('jenv shell ...') doesn't directly modify the parent shell environment.")
        console.print("The actual change is handled by 'jenv init -' shell integration.")
    else:
        err_console.print(f"JDK version '{version_name}' not found.")
        raise typer.Exit(code=1)


@app.command(name="which", help="Display the full path to an executable from the currently active Java version's bin directory.")
def which_command(
    command_name: str = typer.Argument(..., help="The executable name (e.g., java, javac).")
):
    """
    Displays the full path to an executable (java, javac, etc.)
    based on the currently active jenv version.
    """
    active_jdk = get_currently_active_jdk()

    if not active_jdk:
        err_console.print("No active Java version found or jenv not fully configured.")
        err_console.print("Try setting a version with 'jenv global/local/shell <version>' or ensure 'java' is in your system PATH.")
        raise typer.Exit(code=1)

    # Determine executable extension for Windows
    executable_name = command_name
    if platform.system() == "Windows":
        # Common Java executables might not always have .exe explicitly, but check for it
        if not command_name.endswith(".exe"):
            executable_name = f"{command_name}.exe"

    cmd_path = active_jdk.path / "bin" / executable_name

    if cmd_path.is_file() and os.access(str(cmd_path), os.X_OK):
        console.print(str(cmd_path))
    else:
        # Fallback for Windows if .exe wasn't initially provided for commands like 'java'
        if platform.system() == "Windows" and not command_name.endswith(".exe"):
            cmd_path_no_ext = active_jdk.path / "bin" / command_name
            if cmd_path_no_ext.is_file() and os.access(str(cmd_path_no_ext), os.X_OK):
                 console.print(str(cmd_path_no_ext))
                 return

        err_console.print(f"Executable '{command_name}' not found in the bin directory of the active JDK: {active_jdk.name} ({active_jdk.path})")
        raise typer.Exit(code=1)

SUPPORTED_SHELLS = ["bash", "zsh", "fish", "powershell", "cmd"] # cmd is for Windows Command Prompt

@app.command(name="init", help="Set up jenv for your shell. Run 'eval \"$(jenv init <shell_name>)\"' for POSIX shells.")
def init_shell(
    shell_name: Optional[str] = typer.Argument(None, help=f"The shell to initialize for. Supported: {', '.join(SUPPORTED_SHELLS)}. Auto-detects if not provided.")
):
    """
    Outputs shell commands to properly initialize jenv.
    These commands should be evaluated by your shell, e.g., by adding:
    eval "$(jenv init bash)" to .bashrc
    eval "$(jenv init zsh)" to .zshrc
    jenv init fish | source to config.fish
    jenv init powershell | Invoke-Expression (for PowerShell profile)
    Call jenv init cmd > jenv_init.bat and run jenv_init.bat (for CMD, less ideal)
    """
    detected_shell = ""
    if not shell_name:
        shell_env = os.environ.get("SHELL")
        if shell_env:
            detected_shell = Path(shell_env).name
        elif platform.system() == "Windows":
            # Powershell often has $env:PSModulePath, CMD has COMSPEC
            if os.environ.get("PSModulePath"):
                detected_shell = "powershell"
            elif os.environ.get("COMSPEC"):
                detected_shell = "cmd"

        if detected_shell not in SUPPORTED_SHELLS:
            err_console.print(f"Could not auto-detect a supported shell. Please specify one: {', '.join(SUPPORTED_SHELLS)}")
            raise typer.Exit(1)
        err_console.print(f"# Auto-detected shell: {detected_shell}") # Print to stderr
        shell_name = detected_shell

    if shell_name not in SUPPORTED_SHELLS:
        err_console.print(f"Unsupported shell: {shell_name}. Supported shells are: {', '.join(SUPPORTED_SHELLS)}")
        raise typer.Exit(1)

    shims_dir = JENV_DIR / "shims"
    jenv_bin_dir = JENV_DIR / "bin" # Assuming jenv might place its own script here eventually

    output_lines = [f"# jenv initialization script for {shell_name}"]

    
    if shell_name in ["bash", "zsh"]:
        output_lines.extend([
            f'export JENV_DIR="{JENV_DIR}"',
            f'export PATH="{shims_dir}:{jenv_bin_dir}:$PATH"',  # Fixed PATH format
            'jenv_shell_set() {',
            '  export JENV_VERSION="$1"',
            '}',
            'jenv_shell_unset() {',
            '  unset JENV_VERSION',
            '}',
        ])
    elif shell_name == "fish":
        output_lines.extend([
            f'set -gx JENV_DIR "{JENV_DIR}"',
            f'fish_add_path -mP "{shims_dir}"',
            f'fish_add_path -mP "{jenv_bin_dir}"',
            '# To be implemented: function for jenv shell, JAVA_HOME',
            '# function jenv_shell_set; set -gx JENV_VERSION $argv[1]; end',
            '# function jenv_shell_unset; functions -e jenv_shell_set; set -e JENV_VERSION; end',
        ])
    elif shell_name == "powershell":
        output_lines.extend([
            f'$Env:JENV_DIR = "{JENV_DIR}"',
            f'$Env:PATH = "{shims_dir};{jenv_bin_dir};" + $Env:PATH',
            '# PowerShell integration needs more work, especially for `jenv shell`',
            '# function Set-JenvShellVersion { param($Version) $Env:JENV_VERSION = $Version }',
            '# function Clear-JenvShellVersion { Remove-Item Env:\\JENV_VERSION }',
        ])
    elif shell_name == "cmd":
        # CMD is tricky for robust PATH modification and functions.
        # Usually done by a .bat file that `call`s another to set env vars.
        output_lines.extend([
            f'@echo off',
            f'set "JENV_DIR={JENV_DIR}"',
            f'set "PATH={shims_dir};{jenv_bin_dir};%PATH%"',
            f'@REM For jenv shell, you might need a helper jenv.bat in PATH that sets JENV_VERSION',
            f'@REM and then calls the actual java. This is complex for CMD.'
        ])

    # Ensure the shims and bin directories exist
    shims_dir.mkdir(parents=True, exist_ok=True)
    jenv_bin_dir.mkdir(parents=True, exist_ok=True)

    # Print the script to stdout
    for line in output_lines:
        console.print(line)

@app.command(name="rehash", help="Re-generates jenv shims for Java executables.")
def rehash_shims():
    """
    Creates or updates shims for common Java executables in the jenv shims directory.
    The shims directory must be in your PATH for jenv to work correctly.
    (Typically added by 'eval \"$(jenv init your_shell)\"').
    """
    shims_dir = JENV_DIR / "shims"
    shims_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Enhance this list, possibly by scanning JDK bin dirs

    active_jdk = get_currently_active_jdk()
    commands_to_shim = []

    if active_jdk:
        jdk_bin_dir = active_jdk.path / "bin"
        if jdk_bin_dir.is_dir():
            for item in jdk_bin_dir.iterdir():
                if item.is_file() and os.access(str(item), os.X_OK):
                    # Add executables, excluding potential .bat or .cmd on non-Windows
                    if platform.system() == "Windows":
                       if item.name.endswith(".exe") or "." not in item.name:
                             commands_to_shim.append(item.name.replace(".exe", "")) # 
                    else: # Linux/macOS
                        if "." not in item.name or item.name.endswith(".sh"): # Avoid shimming e.g. .dylib or other non-direct executables
                             commands_to_shim.append(item.name)
            common_java_commands = ["java", "javac", "jar", "javadoc", "javap", "jps", "jstat", "jconsole", "jdb", "jshell"]
            for cmd in common_java_commands:
                if cmd not in commands_to_shim and (jdk_bin_dir / cmd).exists():
                    commands_to_shim.append(cmd)
            commands_to_shim = sorted(list(set(commands_to_shim))) # Unique and sorted

    if not commands_to_shim: # Fallback if no active JDK or bin dir is empty/unreadable
        logger.warning("No active JDK found or its bin directory is inaccessible. Using a default list of commands for shims.")
        commands_to_shim = ["java", "javac", "jar", "javadoc", "javap", "jps", "jstat", "jconsole", "jdb", "jshell"]


    # This is a placeholder for where the `jenv` executable is.
    # In a real installation, this path would be resolved correctly (e.g. sys.executable if jenv is a script, or a known install path)
    # For development, this is tricky. If we run `poetry run jenv rehash`, the shims need to call `jenv` not `poetry run jenv`.
    # This implies `jenv` must be installed in a way that it's directly on the PATH.
    jenv_executable_in_shim = "jenv"

    shim_template_posix = f"""#!/usr/bin/env sh
# jenv shim for {{command_name}}
# Generated by 'jenv rehash'
set -e
exec "{jenv_executable_in_shim}" internal exec "{{command_name}}" "$@"
"""

    shim_template_windows_bat = f"""@echo off
REM jenv shim for %~n0
REM Generated by 'jenv rehash'
"{jenv_executable_in_shim}" internal exec "%~n0" %*
"""

    created_shims = 0
    updated_shims = 0

    for command_name in commands_to_shim:
        shim_path = shims_dir / command_name
        is_update = shim_path.exists()

        try:
            if platform.system() == "Windows":
                # Create a .bat shim as well for Windows for commands that might be called without .exe
                # The primary shim (no extension) might also work if shims_dir is in PATH and PATHEXT includes empty.
                bat_shim_path = shims_dir / f"{command_name}.bat"
                shim_content_bat = shim_template_windows_bat # Uses %~n0 for command name

                # Write the .bat shim
                with open(bat_shim_path, "w") as f:
                    f.write(shim_content_bat)
                
                if not command_name.endswith('.bat'): # Avoid double .bat.bat
                    with open(shim_path, "w") as f: # 
                         f.write(shim_template_posix.format(command_name=command_name))


            else: # POSIX systems
                shim_content_posix = shim_template_posix.format(command_name=command_name)
                with open(shim_path, "w") as f:
                    f.write(shim_content_posix)
                os.chmod(shim_path, 0o755) # rwxr-xr-x

            if is_update:
                updated_shims +=1
            else:
                created_shims +=1
        except Exception as e:
            err_console.print(f"Failed to create/update shim for {command_name}: {e}")

    if created_shims or updated_shims:
        console.print(f"Rehashed {created_shims+updated_shims} shims ({created_shims} new, {updated_shims} updated) in {shims_dir}.")
    else:
        console.print(f"No shims were created or updated. Shims directory: {shims_dir}")
        if not commands_to_shim:
             console.print("This might be because no active JDK was found or no common commands were identified.")


# Hidden internal commands
# (Existing internal_app and its commands remain here)

@app.command(name="scan", help="Scan for Java installations and manage custom search paths.")
def scan_jdks(
    add_path: Optional[Path] = typer.Option(None, "--add-path", help="Add a custom path to search for JDKs.", resolve_path=True),
    remove_path: Optional[Path] = typer.Option(None, "--remove-path", help="Remove a path from the custom search list.", resolve_path=True),
    list_paths_flag: bool = typer.Option(False, "--list-paths", help="List the configured custom search paths.") # Renamed to avoid conflict
):
    """
    Scans for JDKs, optionally adding or removing custom search paths.
    If no options are provided, performs a scan and lists discovered JDKs.
    Custom paths are stored in ~/.jenv/paths.
    """
    custom_paths_file = JENV_CUSTOM_PATHS_FILE
    current_custom_paths: List[Path] = [] # Use a different variable name

    # Ensure JENV_DIR exists
    JENV_DIR.mkdir(parents=True, exist_ok=True)

    if custom_paths_file.exists():
        try:
            with open(custom_paths_file, "r") as f:
                for line in f:
                    path_str = line.strip()
                    if path_str and not path_str.startswith("#"):
                        current_custom_paths.append(Path(path_str))
        except IOError as e:
            err_console.print(f"Error reading custom paths file {custom_paths_file}: {e}")

    path_management_action = False # Flag to indicate if add/remove was performed

    if add_path:
        path_management_action = True
        if not add_path.is_dir():
            err_console.print(f"Error: Path '{add_path}' is not a valid directory.")
            raise typer.Exit(code=1)

        abs_add_path = add_path.resolve()
        if abs_add_path not in current_custom_paths:
            current_custom_paths.append(abs_add_path)
            current_custom_paths.sort() # Keep paths sorted
            try:
                with open(custom_paths_file, "w") as f:
                    for p in current_custom_paths:
                        f.write(str(p) + "\n")
                console.print(f"Added custom search path: {abs_add_path}")
            except IOError as e:
                err_console.print(f"Error writing to custom paths file {custom_paths_file}: {e}")
                raise typer.Exit(code=1)
        else:
            console.print(f"Path '{abs_add_path}' is already in the custom search list.")

    if remove_path:
        path_management_action = True
        abs_remove_path = remove_path.resolve()
        if abs_remove_path in current_custom_paths:
            current_custom_paths.remove(abs_remove_path)
            try:
                with open(custom_paths_file, "w") as f:
                    for p in current_custom_paths:
                        f.write(str(p) + "\n")
                console.print(f"Removed custom search path: {abs_remove_path}")
                if not current_custom_paths and custom_paths_file.exists():
                    custom_paths_file.unlink()
                    console.print(f"Removed empty custom paths file: {custom_paths_file}")
            except IOError as e:
                err_console.print(f"Error writing to custom paths file {custom_paths_file}: {e}")
                raise typer.Exit(code=1)
        else:
            console.print(f"Path '{abs_remove_path}' not found in the custom search list.")

    if list_paths_flag or path_management_action:
        console.print("\nConfigured custom search paths:")
        if current_custom_paths:
            for p in current_custom_paths:
                console.print(f"  - {p}")
        else:
            console.print("  No custom search paths configured.")
        # If any path management was done (add/remove) OR if only list_paths was specified, then exit.
        if path_management_action or list_paths_flag:
            raise typer.Exit(0) # Successful exit

    # Default action: scan and list JDKs if no path options were given.
    console.print("\nScanning for Java Development Kits...")
    try:
        list_versions(verbose=True) # Pass verbose=True for a more detailed scan output
    except typer.Exit:
        pass # list_versions might exit (e.g., if no JDKs found), allow this.


internal_app = typer.Typer(
    name="internal",
    help="Internal jenv commands (not for direct user execution).",
    hidden=True,
    context_settings={"ignore_unknown_options": True, "allow_interspersed_args": False}
)
app.add_typer(internal_app)

@internal_app.command(
    "exec",
    help="Execute a command from the active JDK. Shim usage: ... exec <cmd> [args...]",
    context_settings={
        "ignore_unknown_options": True, # Crucial for pass-through args
        "allow_interspersed_args": False, # After command_name, no more options for jenv itself
        "help_option_names": [], # Disable --help for this specific subcommand
    }
)
def internal_exec_command(
    command_name: str = typer.Argument(..., help="The executable name to run."),
    command_args: List[str] = typer.Argument(None, help="Arguments for the command."),
):
    """
    Internal command called by shims.
    Determines the active JDK, sets JAVA_HOME, and executes the target command.
    """
    active_jdk = get_currently_active_jdk()

    if not active_jdk:
        err_console.print(f"jenv: No active Java version determined for command '{command_name}'.")
        err_console.print("jenv: Please set a version using 'jenv global/local/shell <version>'.")
        raise typer.Exit(code=127) # Command not found exit code

    # Determine executable extension for Windows
    executable_name_to_find = command_name
    if platform.system() == "Windows" and not command_name.lower().endswith(".exe"):
        executable_name_to_find = f"{command_name}.exe"

    cmd_path = active_jdk.path / "bin" / executable_name_to_find

    if not (cmd_path.is_file() and os.access(str(cmd_path), os.X_OK)):
        # Fallback for Windows if .exe wasn't initially provided
        if platform.system() == "Windows" and executable_name_to_find.lower().endswith(".exe"):
            cmd_path_no_ext = active_jdk.path / "bin" / command_name
            if cmd_path_no_ext.is_file() and os.access(str(cmd_path_no_ext), os.X_OK):
                cmd_path = cmd_path_no_ext
            else:
                err_console.print(f"jenv: Executable '{command_name}' not found in active JDK '{active_jdk.name}' ({active_jdk.path / 'bin'}).")
                raise typer.Exit(code=127)
        else:
            err_console.print(f"jenv: Executable '{command_name}' not found in active JDK '{active_jdk.name}' ({active_jdk.path / 'bin'}).")
            raise typer.Exit(code=127)

    # Set JAVA_HOME for the child process
    env = os.environ.copy()
    env["JAVA_HOME"] = str(active_jdk.path)

    # Add the JDK's bin to PATH as well, in case the executed command needs to find other tools from its own JDK
    # Prepend it to ensure it's found first.
    jdk_bin_path = str(active_jdk.path / "bin")
    env["PATH"] = f"{jdk_bin_path}{os.pathsep}{env.get('PATH', '')}"


    # Prepare arguments for execvpe: first arg is the command itself
    args_for_exec = [str(cmd_path)] + (command_args if command_args else [])

    logger.debug(f"jenv internal exec: Executing '{cmd_path}' with args {args_for_exec} and JAVA_HOME='{active_jdk.path}'")

    try:
        # Replace jenv process with the target command
        if platform.system() == "Windows":
            completed_process = subprocess.run(args_for_exec, env=env, check=False) # check=False to handle exit code manually
            raise typer.Exit(completed_process.returncode)
        else:
            os.execvpe(str(cmd_path), args_for_exec, env)
    except FileNotFoundError:
        err_console.print(f"jenv: Command not found during exec: {cmd_path}")
        raise typer.Exit(code=127)
    except Exception as e:
        err_console.print(f"jenv: Failed to execute command '{command_name}': {e}")
        raise typer.Exit(code=126) # Command invokeable but cannot execute


@app.command(name="install", help="Download and install a JDK version.")
def install_jdk(
    version: str = typer.Argument(..., help="Version to install (e.g., 17, 21, 11)"),
    vendor: str = typer.Option("temurin", "--vendor", "-v", help="JDK vendor (temurin, openjdk)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if already installed"),
):
    """Download and install a JDK version from a supported vendor."""
    try:
        downloader = JdkDownloader()
        
        with console.status(f"Installing {vendor} JDK {version}..."):
            install_path = downloader.download_jdk(version, vendor, force)
        
        console.print(f"✅ Successfully installed {vendor} JDK {version}")
        console.print(f"📁 Installation path: {install_path}")
        console.print(f"💡 Use 'jenv global {vendor}-{version}' to set as default")
        
    except DownloadError as e:
        err_console.print(f"❌ Failed to install {vendor} JDK {version}: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"❌ Unexpected error: {e}")
        raise typer.Exit(code=1)


@app.command(name="install-maven", help="Download and install a Maven version.")
def install_maven(
    version: str = typer.Argument(..., help="Maven version to install (e.g., 3.9.6)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if already installed"),
):
    """Download and install a Maven version."""
    try:
        downloader = MavenDownloader()
        
        with console.status(f"Installing Maven {version}..."):
            install_path = downloader.download_maven(version, force)
        
        console.print(f"✅ Successfully installed Maven {version}")
        console.print(f"📁 Installation path: {install_path}")
        console.print(f"💡 Add {install_path}/bin to your PATH to use Maven")
        
    except DownloadError as e:
        err_console.print(f"❌ Failed to install Maven {version}: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"❌ Unexpected error: {e}")
        raise typer.Exit(code=1)


@app.command(name="list-remote", help="List available JDK versions for download.")
def list_remote_versions(
    vendor: str = typer.Option("temurin", "--vendor", "-v", help="JDK vendor (temurin, openjdk)"),
    jdk: bool = typer.Option(True, "--jdk/--no-jdk", help="Show JDK versions"),
    maven: bool = typer.Option(False, "--maven", help="Show Maven versions"),
):
    """List available versions for download from supported vendors."""
    try:
        if maven:
            console.print("📦 Available Maven Versions:")
            downloader = MavenDownloader()
            versions = downloader.list_available_versions()
            if versions:
                for version in versions[:10]:  # Show first 10
                    console.print(f"  • {version}")
                if len(versions) > 10:
                    console.print(f"  ... and {len(versions) - 10} more")
            else:
                console.print("  No versions found")
        
        if jdk:
            console.print(f"☕ Available {vendor.title()} JDK Versions:")
            downloader = JdkDownloader()
            versions = downloader.list_available_versions(vendor)
            if versions:
                for version in versions[:15]:  # Show first 15
                    console.print(f"  • {version}")
                if len(versions) > 15:
                    console.print(f"  ... and {len(versions) - 15} more")
            else:
                console.print("  No versions found")
                
    except Exception as e:
        err_console.print(f"❌ Failed to list remote versions: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
