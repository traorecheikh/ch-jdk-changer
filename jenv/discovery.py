import platform
import subprocess
from pathlib import Path
import re
import os
from typing import List, Optional, Dict, NamedTuple
import logging

logger = logging.getLogger(__name__)

class JdkInfo(NamedTuple):
    version: str
    name: str # e.g., temurin-17.0.5, openjdk-11.0.16
    path: Path
    vendor: Optional[str] = None # e.g., Temurin, Oracle, OpenJDK
    is_jenv_managed: bool = False # Was it installed by jenv into VERSIONS_DIR?

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        if not isinstance(other, JdkInfo):
            return NotImplemented
        return self.path == other.path

    @property
    def major_version(self) -> Optional[int]:
        match = re.match(r"(\d+)", self.version)
        return int(match.group(1)) if match else None


def get_java_version_from_path(java_home: Path) -> Optional[str]:
    """
    Gets the Java version string from a given JAVA_HOME path.
    """
    logger.debug(f"get_java_version_from_path: Checking JDK at {java_home}")
    java_exe_name = "java.exe" if platform.system() == "Windows" else "java"
    java_exe = java_home / "bin" / java_exe_name

    if not java_exe.exists():
        logger.debug(f"get_java_version_from_path: {java_exe} does not exist.")
        return None
    logger.debug(f"get_java_version_from_path: Found {java_exe}, attempting to get version.")

    try:
        # The -XshowSettings:properties -version command prints to stderr
        result = subprocess.run([str(java_exe), "-XshowSettings:properties", "-version"], capture_output=True, text=True, timeout=5)
        # Prioritize java.runtime.version for full version, fallback to java.version
        version_match = re.search(r"java\.runtime\.version = (.*)", result.stderr)
        if not version_match: # Fallback for older JDKs or different formats
            version_match = re.search(r"java\.version = (.*)", result.stderr)

        if version_match:
            raw_version = version_match.group(1).strip()
            # Clean common suffixes like "+12", "-LTS" if they are not part of the core version number
            # Example: 17.0.3+7, 11.0.12-LTS -> 17.0.3, 11.0.12
            # This is a simple heuristic and might need refinement
            cleaned_version = re.sub(r"([^\-+\s]+).*", r"\1", raw_version) # Escaped hyphen
            logger.debug(f"get_java_version_from_path: Extracted raw version '{raw_version}', cleaned to '{cleaned_version}' for {java_home}")
            return cleaned_version
        # else, if version_match was None from the start or after fallback

    except (subprocess.TimeoutExpired, FileNotFoundError, UnicodeDecodeError) as e:
        logger.warning(f"Could not determine version for {java_home}: {e}")
        return None # This is the return for the except block

    # This is reached if try completed without returning (i.e. version_match was None)
    logger.debug(f"get_java_version_from_path: No version found in output for {java_home}")
    return None # Default return if no version string was parsed

def get_jdk_name_and_vendor(java_home: Path, version: Optional[str]) -> (str, Optional[str]):
    """
    Generates a descriptive name and attempts to identify vendor for a JDK.
    e.g., "temurin-17.0.5", "Oracle"
    """
    name_parts = []
    vendor = None
    path_str = str(java_home).lower()
    dir_name_lower = java_home.name.lower()

    # Specific vendor keywords first
    if "temurin" in path_str or "adoptium" in dir_name_lower: # More specific for adoptium
        vendor = "Temurin"
    elif "oracle" in path_str or (dir_name_lower.startswith("jdk-") and "openjdk" not in dir_name_lower): # Oracle if starts with jdk- and not openjdk
        vendor = "Oracle"
    elif "amazon-corretto" in path_str or "corretto" in dir_name_lower:
        vendor = "Amazon Corretto"
    elif "zulu" in dir_name_lower: # General zulu check
        vendor = "Zulu" # Simplified from "Azul Zulu" for shorter name
    elif "graalvm" in dir_name_lower:
        vendor = "GraalVM"
    elif "openjdk" in dir_name_lower or "openjdk" in path_str: # More specific check for openjdk in dir name or path
        vendor = "OpenJDK"
    # Fallback for generic "jdk" or "java-" names if no other vendor matched and not clearly OpenJDK from above
    elif (dir_name_lower.startswith("jdk") or "java-" in dir_name_lower) and not vendor:
        vendor = "OpenJDK"

    current_name_part = ""
    if vendor:
        current_name_part = vendor.lower().replace(" ", "")
    else:
        # Fallback to part of the directory name if no clear vendor
        # Sanitize directory name for use as a prefix
        sanitized_dir_name = re.sub(r"[^a-zA-Z0-9-]+", "-", dir_name_lower)
        sanitized_dir_name = sanitized_dir_name.strip("-")
        current_name_part = sanitized_dir_name

    name_parts.append(current_name_part)

    if version:
        name_parts.append(version)

    name = "-".join(filter(None, name_parts))
    # Final sanitize for the whole name
    name = re.sub(r"[^a-zA-Z0-9.-]+", "-", name)
    name = name.strip("-")
    # Replace underscores from version with hyphens for consistency in names
    name = name.replace("_", "-")

    return name if name else java_home.name, vendor


def discover_system_jdks() -> List[JdkInfo]:
    """
    Discovers JDK installations on the system.
    This is a basic implementation and can be expanded.
    """
    found_jdks = set()
    search_paths = []

    logger.debug("discover_system_jdks: Starting JDK discovery.")
    # 1. Common environment variables
    for env_var in ["JAVA_HOME", "JDK_HOME"]:
        path_str = os.environ.get(env_var)
        logger.debug(f"discover_system_jdks: Checking env var {env_var}: value '{path_str}'")
        if path_str:
            path = Path(path_str)
            java_exe_standard = path / "bin" / "java"
            java_exe_windows = path / "bin" / "java.exe"
            logger.debug(f"discover_system_jdks: Path from {env_var} is {path}. Checking for java executables...")
            if java_exe_standard.exists() or java_exe_windows.exists():
                logger.debug(f"discover_system_jdks: Found java executable in {path / 'bin'}. Resolving path.")
                 # Resolve symlinks for JAVA_HOME if it points to one
                try:
                    resolved_path = path.resolve(strict=True)
                    search_paths.append(resolved_path)
                    logger.debug(f"discover_system_jdks: Added resolved path {resolved_path} from {env_var} to search_paths.")
                except (FileNotFoundError, RuntimeError) as e: # RuntimeError for deep symlink recursion on some OS
                    search_paths.append(path)
                    logger.warning(f"discover_system_jdks: Could not resolve {path} from {env_var} (error: {e}). Added non-resolved path {path} to search_paths.")
            else:
                logger.debug(f"discover_system_jdks: No java executable found in {path / 'bin'} for {env_var}.")


    # 2. Common installation directories
    system = platform.system() # Define before use
    logger.debug(f"discover_system_jdks: Current system is {system}.")
    if system == "Windows":
        program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
        search_paths.extend([
            program_files / "Java",
            program_files_x86 / "Java",
            program_files / "AdoptOpenJDK",
            program_files / "Microsoft\\jdk", # For Microsoft Build of OpenJDK
            Path(os.environ.get("ChocolateyInstall", "C:/ProgramData/chocolatey")) / "lib", # For choco installs
        ])
        # Scoop path
        scoop_home = Path.home() / "scoop" / "apps"
        if scoop_home.is_dir():
            for app_dir in scoop_home.iterdir():
                if "java" in app_dir.name.lower() or "jdk" in app_dir.name.lower() or "openjdk" in app_dir.name.lower():
                    # Scoop often has a 'current' symlink, and versioned directories
                    if (app_dir / "current").exists():
                        search_paths.append(app_dir / "current")
                    else: # Add versioned dirs directly
                        for version_dir in app_dir.iterdir():
                            if version_dir.is_dir():
                                search_paths.append(version_dir)


    elif system == "Darwin": # macOS
        search_paths.extend([
            Path("/Library/Java/JavaVirtualMachines"),
            Path.home() / ".sdkman/candidates/java", # SDKMAN
            Path("/opt/homebrew/opt"), # Homebrew on Apple Silicon
            Path("/usr/local/opt"),    # Homebrew on Intel Macs
        ])
    elif system == "Linux":
        search_paths.extend([
            Path("/usr/lib/jvm"),
            Path("/usr/java"),
            Path.home() / ".sdkman/candidates/java", # SDKMAN
        ])

    # 3. jenv managed versions
    from jenv.settings import VERSIONS_DIR, JENV_CUSTOM_PATHS_FILE # Avoid circular import at top level
    if VERSIONS_DIR.exists():
        logger.debug(f"discover_system_jdks: Adding JENV managed versions dir {VERSIONS_DIR} to search_paths.")
        search_paths.append(VERSIONS_DIR)
    else:
        logger.debug(f"discover_system_jdks: JENV managed versions dir {VERSIONS_DIR} does not exist.")

    # 4. User-defined custom paths
    logger.debug(f"discover_system_jdks: Checking for custom paths file at {JENV_CUSTOM_PATHS_FILE}.")
    if JENV_CUSTOM_PATHS_FILE.exists():
        logger.debug(f"discover_system_jdks: Custom paths file found. Reading paths.")
        try:
            with open(JENV_CUSTOM_PATHS_FILE, "r") as f:
                for line in f:
                    custom_path_str = line.strip()
                    if custom_path_str and not custom_path_str.startswith("#"):
                        custom_path = Path(custom_path_str)
                        if custom_path.is_dir(): # Check if it's a directory
                            search_paths.append(custom_path)
                        else:
                            logger.warning(f"Custom path '{custom_path_str}' from {JENV_CUSTOM_PATHS_FILE} is not a valid directory or does not exist.")
        except IOError as e:
            logger.error(f"Error reading custom paths file {JENV_CUSTOM_PATHS_FILE}: {e}")


    processed_paths = set()
    logger.debug(f"discover_system_jdks: Compiled search_paths (before processing): {search_paths}")

    for base_path in search_paths:
        logger.debug(f"discover_system_jdks: Processing base_path: {base_path}")
        if not base_path.exists() or not base_path.is_dir():
            logger.debug(f"discover_system_jdks: Base path {base_path} does not exist or is not a dir. Skipping.")
            continue

        # Check if base_path itself is a JDK home
        # Must resolve symlinks here to avoid duplicate entries from different symlink paths
        try:
            resolved_base_path = base_path.resolve(strict=True)
        except (FileNotFoundError, RuntimeError):
            resolved_base_path = base_path # Use original if resolve fails

        if resolved_base_path in processed_paths:
            continue

        is_jenv_managed = str(VERSIONS_DIR) in str(resolved_base_path)

        java_exe = resolved_base_path / "bin" / ("java.exe" if system == "Windows" else "java")
        logger.debug(f"discover_system_jdks: Checking if {resolved_base_path} is a JDK home (java exe: {java_exe}).")
        if java_exe.is_file(): # Check if it's a file, not just exists, to ensure it's not a dir named 'java'
            logger.debug(f"discover_system_jdks: {java_exe} is a file. Getting version...")
            version_str = get_java_version_from_path(resolved_base_path)
            if version_str:
                name, vendor = get_jdk_name_and_vendor(resolved_base_path, version_str)
                logger.info(f"discover_system_jdks: Found JDK: Name={name}, Version={version_str}, Path={resolved_base_path}, Vendor={vendor}")
                found_jdks.add(JdkInfo(version_str, name, resolved_base_path, vendor, is_jenv_managed))
                processed_paths.add(resolved_base_path)
                continue # Don't iterate inside if this base_path is a JDK itself
            else:
                logger.debug(f"discover_system_jdks: Could not get version from {resolved_base_path}, though java exe exists.")
        else:
            logger.debug(f"discover_system_jdks: {java_exe} is not a file or does not exist. Not a JDK home.")


        # If base_path is a directory containing multiple JDKs (e.g. /usr/lib/jvm)
        # or a symlink to such a directory
        logger.debug(f"discover_system_jdks: Checking if {resolved_base_path} is a directory of JDKs.")
        if resolved_base_path.is_dir(): # Check again after potential resolution
            for item in resolved_base_path.iterdir():
                logger.debug(f"discover_system_jdks: Iterating item: {item} in {resolved_base_path}")
                if item.is_dir(): # Could be symlink to dir
                    try:
                        resolved_item_path = item.resolve(strict=True)
                        logger.debug(f"discover_system_jdks: Resolved item {item} to {resolved_item_path}")
                    except (FileNotFoundError, RuntimeError) as e:
                        resolved_item_path = item
                        logger.warning(f"discover_system_jdks: Could not resolve item {item} (error: {e}). Using original path.")

                    if resolved_item_path in processed_paths:
                        logger.debug(f"discover_system_jdks: Path {resolved_item_path} already processed. Skipping.")
                        continue

                    java_exe_in_item = resolved_item_path / "bin" / ("java.exe" if system == "Windows" else "java")
                    logger.debug(f"discover_system_jdks: Checking item {resolved_item_path} as JDK home (java exe: {java_exe_in_item}).")
                    if java_exe_in_item.is_file(): # Check if it's a file
                        logger.debug(f"discover_system_jdks: {java_exe_in_item} is a file. Getting version...")
                        version_str = get_java_version_from_path(resolved_item_path)
                        if version_str:
                            name, vendor = get_jdk_name_and_vendor(resolved_item_path, version_str)
                            is_item_jenv_managed = str(VERSIONS_DIR) in str(resolved_item_path)
                            logger.info(f"discover_system_jdks: Found JDK: Name={name}, Version={version_str}, Path={resolved_item_path}, Vendor={vendor}, Managed={is_item_jenv_managed}")
                            found_jdks.add(JdkInfo(version_str, name, resolved_item_path, vendor, is_item_jenv_managed))
                            processed_paths.add(resolved_item_path)
                        else:
                            logger.debug(f"discover_system_jdks: Could not get version from {resolved_item_path}, though java exe exists.")
                    else:
                        logger.debug(f"discover_system_jdks: {java_exe_in_item} is not a file or does not exist. Not a JDK home.")
                else:
                    logger.debug(f"discover_system_jdks: Item {item} in {resolved_base_path} is not a directory. Skipping.")

    sorted_jdks = sorted(list(found_jdks), key=lambda jdk: (jdk.version, jdk.name), reverse=True)
    logger.debug(f"discover_system_jdks: Discovery finished. Found {len(sorted_jdks)} JDKs: {sorted_jdks}")
    return sorted_jdks

if __name__ == "__main__":
    # For basic testing
    logging.basicConfig(level=logging.INFO)
    jdks = discover_system_jdks()
    if jdks:
        print("Discovered JDKs:")
        for jdk in jdks:
            print(f"  - Version: {jdk.version}, Name: {jdk.name}, Path: {jdk.path}, Vendor: {jdk.vendor}, Managed: {jdk.is_jenv_managed}")
    else:
        print("No JDKs discovered.")
