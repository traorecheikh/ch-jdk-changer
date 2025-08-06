# jenv Installation Script for Windows PowerShell
# 
# Run this script in PowerShell as Administrator (recommended) or regular user
#

param(
    [string]$InstallDir = "$env:USERPROFILE\.jenv",
    [switch]$Force
)

# Colors and formatting
function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($Message) { Write-ColorOutput Green "✅ $Message" }
function Write-Warning($Message) { Write-ColorOutput Yellow "⚠️  $Message" }
function Write-Error($Message) { Write-ColorOutput Red "❌ $Message" }
function Write-Info($Message) { Write-ColorOutput Blue "🔧 $Message" }

Write-Info "Installing jenv - Java Environment Manager"
Write-Info "Installation directory: $InstallDir"

# Check if Python is installed
function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.") {
            Write-Success "Python 3 is already installed: $pythonVersion"
            return $true
        }
    } catch {
        # Python not found
    }
    
    try {
        $pythonVersion = python3 --version 2>&1
        if ($pythonVersion -match "Python 3\.") {
            Write-Success "Python 3 is already installed: $pythonVersion"
            # Create python alias if only python3 exists
            $pythonPath = (Get-Command python3).Source
            $pythonDir = Split-Path $pythonPath
            if (-not (Test-Path "$pythonDir\python.exe")) {
                Copy-Item $pythonPath "$pythonDir\python.exe" -Force
            }
            return $true
        }
    } catch {
        # Python3 not found either
    }
    
    return $false
}

# Install Python using winget or chocolatey
function Install-Python {
    Write-Warning "Python 3 not found. Attempting to install..."
    
    # Try winget first (Windows 10/11)
    try {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Info "Installing Python via winget..."
            winget install Python.Python.3.12
            # Refresh PATH
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
            return Test-PythonInstallation
        }
    } catch {
        Write-Warning "winget installation failed"
    }
    
    # Try chocolatey
    try {
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            Write-Info "Installing Python via chocolatey..."
            choco install python3 -y
            # Refresh PATH
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
            return Test-PythonInstallation
        }
    } catch {
        Write-Warning "chocolatey installation failed"
    }
    
    Write-Error "Could not install Python automatically."
    Write-Info "Please install Python 3 from https://python.org and re-run this script."
    return $false
}

# Create jenv directories
function New-JenvDirectories {
    $dirs = @("$InstallDir", "$InstallDir\bin", "$InstallDir\shims", "$InstallDir\versions")
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "Created directory: $dir"
        }
    }
}

# Install jenv Python package
function Install-JenvPackage {
    Write-Info "Installing jenv Python package..."
    
    try {
        # Try from PyPI first
        python -m pip install jenv-java --user
        Write-Success "Installed jenv from PyPI"
        return $true
    } catch {
        Write-Warning "PyPI installation failed, trying GitHub..."
    }
    
    try {
        # Try from GitHub
        python -m pip install --user git+https://github.com/traorecheikh/ch-jdk-changer.git
        Write-Success "Installed jenv from GitHub"
        return $true
    } catch {
        Write-Warning "GitHub installation failed, trying manual download..."
    }
    
    try {
        # Download and install manually
        $tempDir = "$env:TEMP\jenv-install"
        if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        
        $zipPath = "$tempDir\jenv.zip"
        Invoke-WebRequest -Uri "https://github.com/traorecheikh/ch-jdk-changer/archive/main.zip" -OutFile $zipPath
        
        Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
        Set-Location "$tempDir\ch-jdk-changer-main"
        python -m pip install --user .
        
        Remove-Item $tempDir -Recurse -Force
        Write-Success "Installed jenv from source"
        return $true
    } catch {
        Write-Error "Failed to install jenv: $_"
        return $false
    }
}

# Create jenv wrapper scripts
function New-JenvWrapper {
    Write-Info "Creating jenv wrapper scripts..."
    
    # PowerShell wrapper
    $psWrapper = @"
#!/usr/bin/env pwsh
# jenv PowerShell wrapper
python -m jenv @args
"@
    $psWrapper | Out-File -FilePath "$InstallDir\bin\jenv.ps1" -Encoding UTF8
    
    # Batch wrapper for CMD
    $batWrapper = @"
@echo off
REM jenv batch wrapper
python -m jenv %*
"@
    $batWrapper | Out-File -FilePath "$InstallDir\bin\jenv.bat" -Encoding ASCII
    
    Write-Success "Created wrapper scripts"
}

# Setup PATH and PowerShell profile
function Set-JenvEnvironment {
    Write-Info "Setting up environment..."
    
    # Add to user PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    $jenvBin = "$InstallDir\bin"
    $jenvShims = "$InstallDir\shims"
    
    if ($currentPath -notlike "*$jenvBin*") {
        $newPath = "$jenvBin;$jenvShims;$currentPath"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        $env:PATH = "$jenvBin;$jenvShims;$env:PATH"
        Write-Success "Added jenv to PATH"
    } else {
        Write-Warning "jenv already in PATH"
    }
    
    # Setup PowerShell profile
    $profileDir = Split-Path $PROFILE -Parent
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    
    $jenvInit = @"

# jenv setup
if (Get-Command jenv -ErrorAction SilentlyContinue) {
    # Initialize jenv (placeholder - implement if needed)
}
"@
    
    if ((Test-Path $PROFILE) -and (Get-Content $PROFILE | Select-String "jenv setup")) {
        Write-Warning "jenv setup already exists in PowerShell profile"
    } else {
        Add-Content -Path $PROFILE -Value $jenvInit
        Write-Success "Added jenv setup to PowerShell profile"
    }
}

# Main installation function
function Install-Jenv {
    # Check if already installed
    if ((Test-Path "$InstallDir\bin\jenv.bat") -and (-not $Force)) {
        Write-Warning "jenv appears to be already installed. Use -Force to reinstall."
        return
    }
    
    # Check Python
    if (-not (Test-PythonInstallation)) {
        if (-not (Install-Python)) {
            Write-Error "Python installation failed. Cannot continue."
            return
        }
    }
    
    # Create directories
    New-JenvDirectories
    
    # Install jenv package
    if (-not (Install-JenvPackage)) {
        Write-Error "jenv package installation failed."
        return
    }
    
    # Create wrappers
    New-JenvWrapper
    
    # Setup environment
    Set-JenvEnvironment
    
    Write-Success "jenv installation completed!"
    Write-Info "🎉 To get started:"
    Write-Info "  1. Restart PowerShell or reload your profile"
    Write-Info "  2. Check available versions: jenv list-remote"
    Write-Info "  3. Install a JDK: jenv install 21"
    Write-Info "  4. Set global version: jenv global temurin-21"
    Write-Info ""
    Write-Info "📚 For more information, visit: https://github.com/traorecheikh/ch-jdk-changer"
}

# Run installation
Install-Jenv