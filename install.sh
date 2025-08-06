#!/usr/bin/env bash
# 
# jenv installation script for Unix-like systems (Linux, macOS)
# 
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default installation directory
JENV_DIR="${JENV_DIR:-$HOME/.jenv}"
TEMP_DIR=$(mktemp -d)

echo -e "${BLUE}🔧 Installing jenv - Java Environment Manager${NC}"
echo -e "${BLUE}Installation directory: ${JENV_DIR}${NC}"

# Create jenv directory
mkdir -p "$JENV_DIR"
mkdir -p "$JENV_DIR/bin"
mkdir -p "$JENV_DIR/shims"
mkdir -p "$JENV_DIR/versions"

# Function to detect package manager and install Python/pip
install_python() {
    if command -v python3 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Python 3 is already installed${NC}"
        return
    fi
    
    echo -e "${YELLOW}📦 Installing Python 3...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew >/dev/null 2>&1; then
            brew install python3
        else
            echo -e "${RED}❌ Homebrew not found. Please install Python 3 manually.${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update && sudo apt-get install -y python3 python3-pip
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y python3 python3-pip
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3 python3-pip
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -S python python-pip
        else
            echo -e "${RED}❌ Could not detect package manager. Please install Python 3 manually.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Unsupported operating system. Please install Python 3 manually.${NC}"
        exit 1
    fi
}

# Function to install jenv using pip
install_jenv() {
    echo -e "${YELLOW}📦 Installing jenv Python package...${NC}"
    
    # Try to install from PyPI (when published) or from git
    if pip3 install jenv-java 2>/dev/null; then
        echo -e "${GREEN}✅ Installed jenv from PyPI${NC}"
    elif pip3 install --user git+https://github.com/traorecheikh/ch-jdk-changer.git 2>/dev/null; then
        echo -e "${GREEN}✅ Installed jenv from GitHub${NC}"
    else
        echo -e "${YELLOW}⚠️  PyPI installation failed, trying alternative method...${NC}"
        # Download the repo and install locally
        cd "$TEMP_DIR"
        if command -v curl >/dev/null 2>&1; then
            curl -L https://github.com/traorecheikh/ch-jdk-changer/archive/main.tar.gz | tar xz
        elif command -v wget >/dev/null 2>&1; then
            wget -O- https://github.com/traorecheikh/ch-jdk-changer/archive/main.tar.gz | tar xz
        else
            echo -e "${RED}❌ Need curl or wget to download jenv${NC}"
            exit 1
        fi
        
        cd ch-jdk-changer-main
        pip3 install --user .
        echo -e "${GREEN}✅ Installed jenv from source${NC}"
    fi
}

# Create a wrapper script in jenv bin directory
create_wrapper() {
    echo -e "${YELLOW}📝 Creating jenv wrapper script...${NC}"
    
    cat > "$JENV_DIR/bin/jenv" << 'EOF'
#!/usr/bin/env bash
# jenv wrapper script
exec python3 -m jenv "$@"
EOF
    
    chmod +x "$JENV_DIR/bin/jenv"
    echo -e "${GREEN}✅ Created jenv wrapper at $JENV_DIR/bin/jenv${NC}"
}

# Function to setup shell integration
setup_shell() {
    local shell_name
    shell_name=$(basename "$SHELL")
    
    echo -e "${YELLOW}🐚 Setting up shell integration for $shell_name...${NC}"
    
    local rc_file
    case "$shell_name" in
        bash)
            rc_file="$HOME/.bashrc"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                rc_file="$HOME/.bash_profile"
            fi
            ;;
        zsh)
            rc_file="$HOME/.zshrc"
            ;;
        fish)
            rc_file="$HOME/.config/fish/config.fish"
            mkdir -p "$(dirname "$rc_file")"
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unknown shell: $shell_name. You'll need to setup integration manually.${NC}"
            return
            ;;
    esac
    
    local setup_line
    case "$shell_name" in
        fish)
            setup_line="fish_add_path -mP \"$JENV_DIR/bin\"; and fish_add_path -mP \"$JENV_DIR/shims\""
            ;;
        *)
            setup_line="export PATH=\"$JENV_DIR/bin:$JENV_DIR/shims:\$PATH\""
            ;;
    esac
    
    if [[ -f "$rc_file" ]] && grep -q "jenv" "$rc_file"; then
        echo -e "${YELLOW}⚠️  jenv setup already exists in $rc_file${NC}"
    else
        echo -e "\n# jenv setup" >> "$rc_file"
        echo "$setup_line" >> "$rc_file"
        if [[ "$shell_name" != "fish" ]]; then
            echo "eval \"\$(jenv init $shell_name)\"" >> "$rc_file"
        fi
        echo -e "${GREEN}✅ Added jenv setup to $rc_file${NC}"
    fi
}

# Main installation
main() {
    install_python
    install_jenv
    create_wrapper
    setup_shell
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    echo -e "\n${GREEN}🎉 jenv installation completed!${NC}"
    echo -e "${BLUE}📖 To get started:${NC}"
    echo -e "  1. Restart your shell or run: source ~/.bashrc (or ~/.zshrc)"
    echo -e "  2. Check available versions: jenv list-remote"
    echo -e "  3. Install a JDK: jenv install 21"
    echo -e "  4. Set global version: jenv global temurin-21"
    echo ""
    echo -e "${BLUE}📚 For more information, visit: https://github.com/traorecheikh/ch-jdk-changer${NC}"
}

# Check if running as root (not recommended)
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  Running as root is not recommended. jenv should be installed per-user.${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Installation cancelled${NC}"
        exit 1
    fi
fi

main