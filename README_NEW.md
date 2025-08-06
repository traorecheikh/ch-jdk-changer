# jenv - Cross-Platform Java Environment Manager

**jenv** is a comprehensive command-line tool for managing multiple Java Development Kit (JDK) installations and Maven versions across Linux, macOS, and Windows. It provides automatic JDK discovery, version switching, and download capabilities - designed to be a full-featured alternative to sdkman.

## Features

### ✨ **Core Version Management**
- **JDK Discovery**: Automatically finds Java installations in common system locations
- **Version Switching**: Global, local (project-specific), and shell-session switching
- **Shim-based Execution**: Seamless Java command interception without manual PATH manipulation

### 🚀 **Download & Installation**
- **JDK Installation**: Download and install JDK versions from major vendors
  - ☕ Temurin (Eclipse Adoptium)
  - ☕ OpenJDK
  - More vendors coming soon (Oracle, Amazon Corretto, Zulu, GraalVM)
- **Maven Support**: Download and install Maven versions
- **Cross-Platform Downloads**: Automatic platform detection and appropriate binary selection

### 🌐 **Cross-Platform Support**
- **Linux**: Full native support with bash/zsh/fish integration
- **macOS**: Complete compatibility with Homebrew and system installations
- **Windows**: PowerShell, CMD, and batch script support

### 🔧 **Advanced Features**
- **Custom JDK Paths**: Add custom directories for JDK scanning
- **Shell Integration**: Deep integration with bash, zsh, fish, PowerShell, and CMD
- **Automatic Shim Generation**: Creates executable shims for Java tools
- **Project-specific Versions**: `.jenv-version` files for per-project Java versions

## Quick Start

### One-Line Installation

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/traorecheikh/ch-jdk-changer/main/install.sh | bash
```

**Windows PowerShell (as Administrator):**
```powershell
iwr -useb https://raw.githubusercontent.com/traorecheikh/ch-jdk-changer/main/install.ps1 | iex
```

### Manual Installation

1. **Install Python 3.8+** (if not already installed)
2. **Install jenv:**
   ```bash
   pip install git+https://github.com/traorecheikh/ch-jdk-changer.git
   ```
3. **Setup shell integration:**
   ```bash
   echo 'eval "$(jenv init bash)"' >> ~/.bashrc  # or ~/.zshrc for zsh
   source ~/.bashrc
   ```

## Usage Examples

### Basic Operations
```bash
# List available JDK versions for download
jenv list-remote

# Install a JDK version
jenv install 21                    # Install latest JDK 21 (Temurin)
jenv install 17 --vendor openjdk  # Install OpenJDK 17

# Install Maven
jenv install-maven 3.9.6

# List installed versions
jenv versions

# Set global default
jenv global temurin-21

# Set project-specific version
jenv local temurin-17

# Set shell session version
jenv shell temurin-11
```

### Advanced Usage
```bash
# Add custom JDK search path
jenv scan --add-path /opt/custom-jdks

# Re-generate shims after manual JDK installation
jenv rehash

# Check currently active version
jenv version

# Find path to java executable
jenv which java
```

## Platform-Specific Features

### Windows Integration

**Enhanced Windows batch script (`ch.bat`):**
- Standalone Java version switcher for Windows
- Automatic JAVA_HOME and PATH management
- Integration with Windows Registry
- Support for both Program Files and custom installations

**PowerShell Integration:**
- Native PowerShell cmdlets and functions
- Windows-specific path handling
- Integration with Windows environment variables

### Linux/Unix Features

**Shell Integration:**
- bash, zsh, fish support
- Automatic shim generation
- Environment variable management
- Seamless integration with package managers

## Supported JDK Vendors

| Vendor | Installation Command | Notes |
|--------|---------------------|-------|
| **Temurin** | `jenv install 21 --vendor temurin` | Eclipse Adoptium (default) |
| **OpenJDK** | `jenv install 17 --vendor openjdk` | Official OpenJDK builds |

*More vendors (Oracle, Amazon Corretto, Azul Zulu, GraalVM) coming soon!*

## Configuration

### Directory Structure
```
~/.jenv/
├── bin/          # jenv executables
├── shims/        # Java command shims
├── versions/     # Downloaded JDK/Maven installations
├── version       # Global version setting
├── paths         # Custom search paths
└── config.toml   # Configuration file
```

### Environment Variables
- `JENV_DIR`: jenv installation directory (default: `~/.jenv`)
- `JENV_VERSION`: Current shell session version
- `JAVA_HOME`: Automatically managed by jenv

## Shell Integration

### Bash/Zsh Setup
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.jenv/bin:$PATH"
eval "$(jenv init bash)"  # or 'zsh' for zsh
```

### Fish Setup
```fish
# Add to ~/.config/fish/config.fish
fish_add_path $HOME/.jenv/bin
jenv init fish | source
```

### PowerShell Setup
```powershell
# Add to PowerShell profile
$env:PATH = "$env:USERPROFILE\.jenv\bin;$env:PATH"
jenv init powershell | Invoke-Expression
```

## Comparison with sdkman

| Feature | jenv | sdkman |
|---------|------|---------|
| **Cross-Platform** | ✅ Linux, macOS, Windows | ❌ Unix-only |
| **JDK Downloads** | ✅ Multiple vendors | ✅ Multiple vendors |
| **Maven Support** | ✅ Yes | ✅ Yes |
| **Local Versions** | ✅ `.jenv-version` files | ✅ `.sdkmanrc` files |
| **Windows Support** | ✅ Native PowerShell/CMD | ❌ WSL only |
| **Lightweight** | ✅ Python-based | ❌ Bash + curl heavy |
| **Performance** | ✅ Fast startup | ❌ Slower initialization |

## Troubleshooting

### Common Issues

**jenv command not found:**
```bash
# Ensure jenv is in PATH
export PATH="$HOME/.jenv/bin:$PATH"
# Re-run shell initialization
eval "$(jenv init bash)"
```

**Download failures:**
```bash
# Check internet connectivity
# Try different vendor
jenv install 17 --vendor openjdk
```

**Windows PATH issues:**
```cmd
# Refresh environment variables
refreshenv
# Or restart command prompt
```

## Development

### Building from Source
```bash
git clone https://github.com/traorecheikh/ch-jdk-changer.git
cd ch-jdk-changer
poetry install
poetry run jenv --help
```

### Running Tests
```bash
poetry run pytest tests/ -v
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/traorecheikh/ch-jdk-changer/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/traorecheikh/ch-jdk-changer/discussions)
- 📚 **Documentation**: [GitHub Wiki](https://github.com/traorecheikh/ch-jdk-changer/wiki)

---

**Crafted with ❤️ by [Cheikh Tidiane](https://github.com/traorecheikh)**

*Making Java development environment management simple and cross-platform.*