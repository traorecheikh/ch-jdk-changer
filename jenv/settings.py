from pathlib import Path
import os

# JENV_DIR is typically ~/.jenv
JENV_DIR = Path(os.environ.get("JENV_DIR", Path.home() / ".jenv"))
VERSIONS_DIR = JENV_DIR / "versions" # For JDKs potentially installed by jenv
CONFIG_FILE = JENV_DIR / "config.toml"

# Ensure base directory exists
JENV_DIR.mkdir(parents=True, exist_ok=True)
VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Environment variable that can be set by 'jenv shell'
JENV_VERSION_ENV_VAR = "JENV_VERSION"
# File for 'jenv local'
JENV_VERSION_FILE = ".jenv-version"
# File for 'jenv global'
JENV_GLOBAL_VERSION_FILE = JENV_DIR / "version"
# File for custom search paths for JDKs
JENV_CUSTOM_PATHS_FILE = JENV_DIR / "paths"
