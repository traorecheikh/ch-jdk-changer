from pathlib import Path
from typing import Optional
import logging
import os
import platform

logger = logging.getLogger(__name__)

def write_version_file(file_path: Path, version_name: str) -> None:
    """Writes the version name to the specified file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(version_name.strip())
    except IOError as e:
        logger.error(f"Error writing version to {file_path}: {e}")
        # Potentially raise a custom exception

def read_version_file(file_path: Path) -> Optional[str]:
    """Reads the version name from the specified file."""
    if file_path.is_file():
        try:
            return file_path.read_text().strip()
        except IOError as e:
            logger.error(f"Error reading version from {file_path}: {e}")
            return None
    return None

def get_active_jdk_path_from_env() -> Optional[Path]:
    """
    Gets the current JAVA_HOME from environment variables if it seems valid.
    """
    java_home_str = os.environ.get("JAVA_HOME")
    if java_home_str:
        java_home_path = Path(java_home_str)
        java_exe = java_home_path / "bin" / ("java.exe" if platform.system() == "Windows" else "java")
        if java_exe.exists():
            return java_home_path.resolve() # Resolve symlinks
    return None

# Add other utility functions as needed, e.g., for symlink management, user prompts.
