"""
JDK and Maven download functionality for jenv.
Supports multiple vendors and platforms.
"""

import platform
import requests
import tarfile
import zipfile
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import json
import logging
import subprocess
import os

from jenv.settings import VERSIONS_DIR

logger = logging.getLogger(__name__)

class DownloadError(Exception):
    """Raised when download or installation fails."""
    pass

class JdkDownloader:
    """Handles JDK downloads from various vendors."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'jenv/0.1.0 (Java Environment Manager)'
        })
    
    def get_system_info(self) -> Tuple[str, str]:
        """Get current system OS and architecture."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Normalize OS names
        if system == "darwin":
            system = "macos"
        elif system == "windows":
            system = "windows"
        else:
            system = "linux"
        
        # Normalize architecture names
        if machine in ["x86_64", "amd64"]:
            arch = "x64"
        elif machine in ["aarch64", "arm64"]:
            arch = "aarch64"
        elif machine in ["i386", "i686"]:
            arch = "x32"
        else:
            arch = machine
            
        return system, arch
    
    def list_available_versions(self, vendor: str = "temurin") -> List[str]:
        """List available JDK versions for a vendor."""
        try:
            if vendor.lower() == "temurin":
                return self._list_temurin_versions()
            elif vendor.lower() == "openjdk":
                return self._list_openjdk_versions()
            else:
                logger.warning(f"Vendor {vendor} not supported yet")
                return []
        except Exception as e:
            logger.error(f"Failed to list versions for {vendor}: {e}")
            return []
    
    def _list_temurin_versions(self) -> List[str]:
        """List available Temurin versions from Adoptium API."""
        url = "https://api.adoptium.net/v3/info/available_releases"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            versions = data.get("available_lts_releases", []) + data.get("available_releases", [])
            return sorted(set(str(v) for v in versions), key=int, reverse=True)
        except Exception as e:
            logger.error(f"Failed to fetch Temurin versions: {e}")
            return ["8", "11", "17", "21"]  # Fallback to common LTS versions
    
    def _list_openjdk_versions(self) -> List[str]:
        """List common OpenJDK versions."""
        return ["8", "11", "17", "21", "22", "23"]
    
    def download_jdk(self, version: str, vendor: str = "temurin", force: bool = False) -> Path:
        """Download and install a JDK version."""
        system, arch = self.get_system_info()
        
        # Create version directory
        version_dir = VERSIONS_DIR / f"{vendor}-{version}"
        if version_dir.exists() and not force:
            logger.info(f"JDK {vendor}-{version} already installed")
            return version_dir
        
        logger.info(f"Downloading {vendor} JDK {version} for {system}-{arch}")
        
        try:
            if vendor.lower() == "temurin":
                download_url, filename = self._get_temurin_download_url(version, system, arch)
            elif vendor.lower() == "openjdk":
                download_url, filename = self._get_openjdk_download_url(version, system, arch)
            else:
                raise DownloadError(f"Vendor {vendor} not supported")
            
            # Download the JDK
            archive_path = self._download_file(download_url, filename)
            
            # Extract to version directory
            if version_dir.exists():
                shutil.rmtree(version_dir)
            version_dir.mkdir(parents=True, exist_ok=True)
            
            self._extract_archive(archive_path, version_dir)
            
            # Clean up download
            archive_path.unlink()
            
            logger.info(f"Successfully installed {vendor} JDK {version} to {version_dir}")
            return version_dir
            
        except Exception as e:
            if version_dir.exists():
                shutil.rmtree(version_dir, ignore_errors=True)
            raise DownloadError(f"Failed to download {vendor} JDK {version}: {e}")
    
    def _get_temurin_download_url(self, version: str, system: str, arch: str) -> Tuple[str, str]:
        """Get Temurin download URL from Adoptium API."""
        api_url = f"https://api.adoptium.net/v3/binary/latest/{version}/ga/{system}/{arch}/jdk/hotspot/normal/eclipse"
        
        try:
            # Get redirect URL which contains the actual download URL
            response = self.session.head(api_url, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                download_url = response.url
                # Extract filename from Content-Disposition header or URL
                filename = None
                if 'content-disposition' in response.headers:
                    import re
                    cd = response.headers['content-disposition']
                    filename_match = re.search(r'filename[*]?=([^;]+)', cd)
                    if filename_match:
                        filename = filename_match.group(1).strip('"\'')
                
                if not filename:
                    # Fallback: create a safe filename
                    filename = f"temurin-{version}-{system}-{arch}.tar.gz"
                    if system == "windows":
                        filename = f"temurin-{version}-{system}-{arch}.zip"
                
                return download_url, filename
            else:
                raise DownloadError(f"No Temurin JDK {version} available for {system}-{arch}")
        except Exception as e:
            raise DownloadError(f"Failed to get Temurin download URL: {e}")
    
    def _get_openjdk_download_url(self, version: str, system: str, arch: str) -> Tuple[str, str]:
        """Get OpenJDK download URL (simplified implementation)."""
        # This is a simplified implementation for common versions
        # In a real implementation, you might scrape jdk.java.net or use other APIs
        
        base_urls = {
            "21": "https://download.java.net/java/GA/jdk21/fd2272bbf8e04c3dbaee13770090416c/35/GPL/",
            "17": "https://download.java.net/java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL/",
            "11": "https://download.java.net/java/GA/jdk11/9/GPL/",
        }
        
        if version not in base_urls:
            raise DownloadError(f"OpenJDK version {version} not available")
        
        # Construct filename based on platform
        if system == "linux":
            suffix = "linux-x64_bin.tar.gz"
        elif system == "macos":
            suffix = "osx-x64_bin.tar.gz"
        elif system == "windows":
            suffix = "windows-x64_bin.zip"
        else:
            raise DownloadError(f"Platform {system} not supported for OpenJDK")
        
        filename = f"openjdk-{version}_{suffix}"
        download_url = base_urls[version] + filename
        
        return download_url, filename
    
    def _download_file(self, url: str, filename: str) -> Path:
        """Download a file from URL."""
        download_path = Path("/tmp") / filename
        
        try:
            logger.info(f"Downloading {filename}...")
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end="", flush=True)
            
            print()  # New line after progress
            logger.info(f"Downloaded {filename} ({downloaded} bytes)")
            return download_path
            
        except Exception as e:
            if download_path.exists():
                download_path.unlink()
            raise DownloadError(f"Failed to download {filename}: {e}")
    
    def _extract_archive(self, archive_path: Path, extract_to: Path):
        """Extract tar.gz or zip archive."""
        try:
            if archive_path.suffix == '.gz' and archive_path.suffixes[-2:] == ['.tar', '.gz']:
                # tar.gz file
                with tarfile.open(archive_path, 'r:gz') as tar:
                    # Get the root directory name to handle nested structure
                    members = tar.getmembers()
                    if members:
                        root_dir = members[0].name.split('/')[0]
                        tar.extractall(extract_to.parent)
                        # Move contents from nested directory to target directory
                        nested_dir = extract_to.parent / root_dir
                        if nested_dir.exists() and nested_dir != extract_to:
                            shutil.move(str(nested_dir), str(extract_to))
            elif archive_path.suffix == '.zip':
                # zip file
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    zip_file.extractall(extract_to.parent)
                    # Handle nested directory structure
                    extracted_items = list(extract_to.parent.iterdir())
                    nested_dirs = [item for item in extracted_items if item.is_dir() and item.name != extract_to.name]
                    if nested_dirs:
                        shutil.move(str(nested_dirs[0]), str(extract_to))
            else:
                raise DownloadError(f"Unsupported archive format: {archive_path}")
                
            logger.info(f"Extracted {archive_path.name} to {extract_to}")
            
        except Exception as e:
            raise DownloadError(f"Failed to extract {archive_path}: {e}")


class MavenDownloader:
    """Handles Maven downloads."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'jenv/0.1.0 (Java Environment Manager)'
        })
    
    def list_available_versions(self) -> List[str]:
        """List available Maven versions."""
        # For simplicity, return common versions
        # In a real implementation, you might scrape Apache Maven site or use their API
        return ["3.9.6", "3.9.5", "3.9.4", "3.8.8", "3.8.7", "3.8.6"]
    
    def download_maven(self, version: str, force: bool = False) -> Path:
        """Download and install Maven."""
        maven_dir = VERSIONS_DIR / f"maven-{version}"
        if maven_dir.exists() and not force:
            logger.info(f"Maven {version} already installed")
            return maven_dir
        
        logger.info(f"Downloading Maven {version}")
        
        try:
            download_url = f"https://archive.apache.org/dist/maven/maven-3/{version}/binaries/apache-maven-{version}-bin.tar.gz"
            filename = f"apache-maven-{version}-bin.tar.gz"
            
            # Download Maven
            archive_path = self._download_file(download_url, filename)
            
            # Extract to version directory
            if maven_dir.exists():
                shutil.rmtree(maven_dir)
            maven_dir.mkdir(parents=True, exist_ok=True)
            
            self._extract_maven(archive_path, maven_dir)
            
            # Clean up download
            archive_path.unlink()
            
            logger.info(f"Successfully installed Maven {version} to {maven_dir}")
            return maven_dir
            
        except Exception as e:
            if maven_dir.exists():
                shutil.rmtree(maven_dir, ignore_errors=True)
            raise DownloadError(f"Failed to download Maven {version}: {e}")
    
    def _download_file(self, url: str, filename: str) -> Path:
        """Download a file from URL."""
        download_path = Path("/tmp") / filename
        
        try:
            logger.info(f"Downloading {filename}...")
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded {filename}")
            return download_path
            
        except Exception as e:
            if download_path.exists():
                download_path.unlink()
            raise DownloadError(f"Failed to download {filename}: {e}")
    
    def _extract_maven(self, archive_path: Path, extract_to: Path):
        """Extract Maven tar.gz archive."""
        try:
            with tarfile.open(archive_path, 'r:gz') as tar:
                # Extract to parent directory first
                tar.extractall(extract_to.parent)
                
                # Find the extracted directory and move it
                for item in extract_to.parent.iterdir():
                    if item.is_dir() and item.name.startswith('apache-maven-') and item != extract_to:
                        shutil.move(str(item), str(extract_to))
                        break
                        
            logger.info(f"Extracted Maven to {extract_to}")
            
        except Exception as e:
            raise DownloadError(f"Failed to extract Maven: {e}")