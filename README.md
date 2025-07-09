# jenv - Java Environment Manager

Crafted with ❤️ by Cheikh Tidiane

**jenv** is a command-line tool to help you manage multiple Java Development Kit (JDK) installations on your system. It allows you to easily list, switch between, and (in the future) install different JDK versions.

Inspired by tools like `rbenv` and `pyenv`.

**Status:** _Under Development_

## Features

*   **Discover JDKs:** Automatically finds Java installations in common system locations and via `JAVA_HOME`.
*   **Version Switching:**
    *   **Global:** Set a default Java version for your user account.
    *   **Local:** Set a Java version for a specific project/directory (using a `.jenv-version` file).
    *   **Shell:** Set a Java version for the current shell session only.
*   **Shim-based Execution:** Uses shims to provide Java executables (`java`, `javac`, etc.) from the active version, without needing to manipulate `JAVA_HOME` directly after initial setup.
*   **Custom JDK Paths:** Allows adding custom directories where your JDKs might be installed.
*   **Cross-Platform (Goal):** Designed to work on Linux, macOS, and Windows. (Current implementation primarily tested on Linux-like environments).

## Installation

**Note:** `jenv` is currently under active development. The primary way to use it is by setting up a development environment. A packaged version for easy end-user installation is planned for the future.

### 1. Development Setup (For Contributors or Advanced Users)

1.  Clone the repository:
    ```bash
    git clone https://github.com/example/jenv.git # Replace with actual URL
    cd jenv
    ```
2.  Install dependencies using Poetry:
    ```bash
    poetry install
    ```
3.  Activate the virtual environment:
    ```bash
    poetry shell
    ```
    This makes the `jenv` command available in your current shell.

### 2. End-User Installation (via pip)

Once `jenv` is published to PyPI (Python Package Index), you can install it using pip:

```bash
pip install jenv
```
jenv rehash

export PATH="$HOME/.jenv/shims:$HOME/.jenv/bin:$PATH"
export JENV_DIR="$HOME/.jenv"
export PATH="$JENV_DIR/shims:$JENV_DIR/bin:$PATH"
eval "$(jenv init zsh)"


Make sure your Python scripts directory is on your system's PATH to run `jenv` directly after installation.

(If you are the developer and have just packaged it, you might install it from a local wheel file first for testing, e.g., `pip install dist/jenv-0.1.0-py3-none-any.whl`)

## Setup

To enable `jenv` to manage your Java versions effectively, you need to integrate it with your shell. Add the appropriate line to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`, `~/.config/fish/config.fish`):

*   **Bash:**
    ```bash
    eval "$(jenv init bash)"
    ```
*   **Zsh:**
    ```bash
    eval "$(jenv init zsh)"
    ```
*   **Fish:**
    ```fish
    jenv init fish | source
    ```
*   **PowerShell (Experimental):** Add to your PowerShell profile (`$PROFILE`):
    ```powershell
    jenv init powershell | Invoke-Expression
    ```
*   **CMD (Windows - Limited Support):**
    The CMD integration is less seamless. `jenv init cmd` will output commands to set environment variables. You might save this to a `.bat` file and run it, or manually set `JENV_DIR` and add `~/.jenv/shims` and `~/.jenv/bin` to your `PATH`.

After adding the line, restart your shell or source the configuration file (e.g., `source ~/.bashrc`).

This setup does the following:
1.  Sets up the `JENV_DIR` environment variable (defaults to `~/.jenv`).
2.  Adds the `jenv` shims directory (`$JENV_DIR/shims`) to your `PATH`. This is how `jenv` intercepts calls to `java`, `javac`, etc.
3.  (Potentially) Adds `jenv`'s own bin directory (`$JENV_DIR/bin`) to your `PATH` if it's not already installed globally.

## Usage

Here are the main commands:

*   `jenv --version`: Display the version of `jenv` itself.
*   `jenv versions` or `jenv list`: List all Java versions discovered by `jenv`.
    *   `--verbose`: Show full paths and vendor information.
    *   The currently active version is marked with an asterisk (`*`).
*   `jenv version` or `jenv current`: Show the currently active Java version and how it was set (global, local, shell, or system `JAVA_HOME`).
*   `jenv global <version_name_or_path>`: Set the global Java version. This version is used when no local or shell version is active.
    *   Example: `jenv global openjdk-11.0.12`
    *   Example: `jenv global /opt/myjdks/jdk-17`
    *   Running `jenv global` without a version argument shows the currently set global version.
*   `jenv local <version_name_or_path>`: Set the Java version for the current directory and its subdirectories. This creates a `.jenv-version` file.
    *   Example: `jenv local temurin-17.0.1`
    *   `--unset`: Remove the `.jenv-version` file from the current directory.
    *   Running `jenv local` without a version argument shows the local version configuration (if any) for the current directory or its parents.
*   `jenv shell <version_name_or_path>`: Set the Java version for the current shell session only. This overrides local and global settings.
    *   Example: `jenv shell my-custom-jdk-8`
    *   `--unset`: Deactivate the shell-specific version.
    *   Requires `jenv init` to be set up for your shell.
*   `jenv which <command>`: Display the full path to an executable (e.g., `java`, `javac`) from the currently active Java version.
    *   Example: `jenv which java`
*   `jenv rehash`: Re-generates the shims for Java executables. Run this if you've installed a new JDK manually in a location that `jenv` now manages, or if executables in a JDK's `bin` directory have changed. `jenv` attempts to automatically find executables in the active JDK's `bin` directory.
*   `jenv scan`: Manually trigger a scan for Java installations.
    *   `--add-path <path>`: Add a custom directory path for `jenv` to search for JDKs. This path is saved for future scans.
    *   `--remove-path <path>`: Remove a previously added custom search path.
    *   `--list-paths`: List all configured custom search paths.
    *   If no path options are given, performs a scan and lists all discovered JDKs (similar to `jenv versions --verbose`).
*   `jenv init <shell_name>`: Outputs the shell script for initialization (see Setup section).

### Version Strings

When specifying a version for `global`, `local`, or `shell`, `jenv` tries to be flexible:
*   You can use the name `jenv` assigns (e.g., `openjdk-11.0.12`, `temurin-17.0.1`). These names are generated based on vendor heuristics and version numbers.
*   You can often use partial versions (e.g., `11`, `17.0`). `jenv` will try to match known installations. If ambiguous, it will list matches.
*   You can provide a direct file system path to a JDK home directory.

## How it Works

`jenv` uses a combination of environment variables, shims, and version files:

1.  **`JENV_DIR`**: The root directory for `jenv`'s files (shims, version files, potentially installed JDKs). Defaults to `~/.jenv`.
2.  **Shims**: When you run `eval "$(jenv init <shell>)"`, a directory (`$JENV_DIR/shims`) is added to the front of your `PATH`. This directory contains small executable scripts (shims) that correspond to Java commands like `java`, `javac`, etc.
3.  When you run a command like `java`, you're actually running a `jenv` shim.
4.  The shim executes `jenv internal exec java [args...]`.
5.  `jenv internal exec` determines the correct Java version to use based on the following precedence:
    1.  **`JENV_VERSION` environment variable**: Set by `jenv shell`.
    2.  **`.jenv-version` file**: Searched in the current directory and then parent directories. Set by `jenv local`.
    3.  **`$JENV_DIR/version` file**: The global version file. Set by `jenv global`.
    4.  If none of the above are set, `jenv` might fall back to system `JAVA_HOME` or what's in `PATH` (though behavior with shims means `jenv` usually controls this).
6.  Once the version is determined, `jenv internal exec` sets the `JAVA_HOME` environment variable appropriately for the chosen JDK and then executes the *actual* Java command from that JDK's `bin` directory.

## Future Features (Planned)

*   `jenv install <version>`: Download and install specific JDK versions from known sources (e.g., Adoptium, OpenJDK.net).
*   `jenv uninstall <version>`: Uninstall JDKs managed by `jenv`.
*   More robust JDK vendor/distribution identification.
*   Support for `.tool-versions` file for compatibility with tools like `asdf`.
*   Windows: More native shim mechanism (e.g., `.exe` shims or better `.bat` script generation).

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

### Development Notes

*   Written in Python using [Typer](https://typer.tiangolo.com/) (based on Click).
*   Uses `poetry` for dependency management and packaging.
*   Tests are written with `pytest`. Run tests with `poetry run pytest`.
*   Code formatting: (Consider Black or Ruff Formatter)
*   Linting: (Consider Ruff or Flake8)

### Building and Publishing (For Developers/Maintainers)

If you are a developer of `jenv` and want to create a distributable package or publish it to PyPI:

1.  **Ensure `pyproject.toml` is up-to-date:**
    *   Verify the `version` number (e.g., increment if releasing a new version).
    *   Ensure author and other metadata are correct.
2.  **Install Poetry** if you haven't already:
    ```bash
    pip install poetry
    ```
3.  **Build the package:**
    This command creates the source archive (sdist) and a wheel file in the `dist/` directory.
    ```bash
    poetry build
    ```
4.  **Check the package (optional but recommended):**
    ```bash
    poetry check
    ```
    You can also use `twine check dist/*` if you have Twine installed.
5.  **Publish to TestPyPI (optional, recommended for testing the publishing process):**
    *   You'll need an account on [TestPyPI](https://test.pypi.org/).
    *   Configure Poetry to use TestPyPI (if you haven't already):
        ```bash
        poetry config repositories.testpypi https://test.pypi.org/legacy/
        ```
    *   Publish, providing your TestPyPI username and password when prompted:
        ```bash
        poetry publish -r testpypi
        ```
    *   You can then try installing from TestPyPI:
        ```bash
        pip install --index-url https://test.pypi.org/simple/ jenv
        ```
6.  **Publish to PyPI (Live):**
    *   You'll need an account on [PyPI](https://pypi.org/).
    *   Ensure you have configured API tokens or username/password with Poetry. Using API tokens is recommended.
    *   Publish to PyPI:
        ```bash
        poetry publish
        ```
        Poetry will prompt for your PyPI credentials (or use a configured API token).

**Important:** Publishing to PyPI is a live release. Ensure the package is stable and the version number is appropriate.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Appendix: `ch.bat` - Simple Windows Java Switcher

This repository also includes `ch.bat`, a lightweight, standalone batch script for quickly switching Java versions on Windows. It is a separate utility from the more comprehensive `jenv` Python application.

For instructions on how to use `ch.bat`, please see its dedicated documentation: [ch.bat Usage (readme.md)](readme.md).
