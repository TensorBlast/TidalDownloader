#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Tidal Downloader
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 🎵
# @raycast.packageName Tidal Downloads
# @raycast.argument1 { "type": "text", "placeholder": "Tidal URL/ID or 'config'", "optional": true }
# @raycast.argument2 { "type": "text", "placeholder": "Config key=value (optional)", "optional": true }
# @raycast.argument3 { "type": "text", "placeholder": "SSH password (optional)", "optional": true }

# Documentation:
# @raycast.description Download from Tidal or manage tidal-dl-ng configuration via SSH
# @raycast.author Your Name
# @raycast.authorURL https://github.com/yourusername

import sys
import os
import re
import json
import subprocess
import getpass
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

# Configuration - Modify these as needed
SSH_CONFIG = {
    "host": "192.168.77.247",
    "user": None,  # Will use current user if not set
    "port": 22,
    "key_path": None,  # e.g., "~/.ssh/id_rsa"
}

# ANSI color codes for better output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text: str, color: str = "", bold: bool = False):
    """Print colored text"""
    if bold:
        print(f"{Colors.BOLD}{color}{text}{Colors.RESET}")
    else:
        print(f"{color}{text}{Colors.RESET}")

def print_header():
    """Print script header"""
    print_colored("🎵 Tidal Downloader via SSH", Colors.CYAN, bold=True)
    print_colored(f"📡 Server: {SSH_CONFIG['host']}", Colors.BLUE)
    print("─" * 50)

def parse_tidal_url(url: str) -> Tuple[str, str]:
    """Extract type and ID from Tidal URL"""
    patterns = {
        'track': r'tidal\.com/(?:browse/)?track/(\d+)',
        'album': r'tidal\.com/(?:browse/)?album/(\d+)',
        'playlist': r'tidal\.com/(?:browse/)?playlist/([a-zA-Z0-9-]+)',
        'video': r'tidal\.com/(?:browse/)?video/(\d+)',
        'artist': r'tidal\.com/(?:browse/)?artist/(\d+)',
    }
    
    for media_type, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            return media_type, match.group(1)
    
    if url.isdigit():
        return 'track', url
    
    raise ValueError(f"Could not parse Tidal URL: {url}")

def build_ssh_command(command: str, password: Optional[str] = None) -> List[str]:
    """Build SSH command with proper parameters"""
    if password:
        # Use sshpass for password authentication
        ssh_cmd = ["sshpass", "-p", password, "ssh"]
    else:
        ssh_cmd = ["ssh"]
    
    # Add SSH options
    ssh_cmd.extend([
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-q"  # Quiet mode
    ])
    
    if SSH_CONFIG["key_path"] and not password:
        ssh_cmd.extend(["-i", str(Path(SSH_CONFIG["key_path"]).expanduser())])
    
    ssh_cmd.extend(["-p", str(SSH_CONFIG["port"])])
    
    user = SSH_CONFIG["user"] or getpass.getuser()
    ssh_cmd.append(f"{user}@{SSH_CONFIG['host']}")
    ssh_cmd.append(command)
    
    return ssh_cmd

def execute_ssh_command(command: str, password: Optional[str] = None, 
                       timeout: int = 300) -> Tuple[str, str, int]:
    """Execute command on remote server via SSH"""
    try:
        ssh_cmd = build_ssh_command(command, password)
        
        # Check if sshpass is needed but not available
        if password and not subprocess.run(["which", "sshpass"], 
                                         capture_output=True).returncode == 0:
            print_colored("⚠️  sshpass not found. Installing via Homebrew...", Colors.YELLOW)
            subprocess.run(["brew", "install", "sshpass"], check=True)
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
        
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except subprocess.CalledProcessError as e:
        return "", f"SSH error: {e}", 1
    except Exception as e:
        return "", str(e), 1

def get_tidal_config(password: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve current tidal-dl-ng configuration"""
    cmd = "cat ~/.config/tidal_dl_ng/settings.json 2>/dev/null || echo '{}'"
    stdout, stderr, exit_code = execute_ssh_command(cmd, password)
    
    try:
        return json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        return {}

def set_tidal_config(key: str, value: str, password: Optional[str] = None) -> bool:
    """Set tidal-dl-ng configuration option"""
    cmd = f'tidal-dl-ng cfg "{key}" "{value}"'
    stdout, stderr, exit_code = execute_ssh_command(cmd, password)
    
    if exit_code == 0:
        print_colored(f"✅ Set {key} = {value}", Colors.GREEN)
        return True
    else:
        print_colored(f"❌ Failed to set {key}: {stderr}", Colors.RED)
        return False

def display_config(config: Dict[str, Any], indent: int = 0):
    """Display configuration in a readable format"""
    for key, value in sorted(config.items()):
        if isinstance(value, dict):
            print("  " * indent + f"{Colors.CYAN}{key}:{Colors.RESET}")
            display_config(value, indent + 1)
        else:
            print("  " * indent + f"{Colors.CYAN}{key}:{Colors.RESET} {value}")

def download_tidal_content(url: str, password: Optional[str] = None) -> bool:
    """Download Tidal content using tidal-dl-ng"""
    try:
        media_type, media_id = parse_tidal_url(url)
        print_colored(f"\n🔍 Detected {media_type} with ID: {media_id}", Colors.BLUE)
    except ValueError as e:
        print_colored(f"❌ {e}", Colors.RED)
        return False
    
    print_colored("\n⬇️  Starting download...", Colors.YELLOW)
    cmd = f'tidal-dl-ng dl "{url}"'
    
    # Execute with real-time output
    ssh_cmd = build_ssh_command(cmd, password)
    
    try:
        process = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, text=True)
        
        # Stream output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        exit_code = process.poll()
        
        if exit_code == 0:
            print_colored("\n✅ Download completed successfully!", Colors.GREEN)
            return True
        else:
            stderr = process.stderr.read()
            print_colored(f"\n❌ Download failed: {stderr}", Colors.RED)
            return False
            
    except Exception as e:
        print_colored(f"\n❌ Error during download: {e}", Colors.RED)
        return False

def show_help():
    """Show usage help"""
    print_colored("\n📖 Usage Examples:", Colors.CYAN, bold=True)
    print("\n1. Download a track:")
    print("   Just paste: https://tidal.com/browse/track/12345678")
    print("\n2. Show configuration:")
    print("   Type: config")
    print("\n3. Set configuration:")
    print("   Arg 1: config")
    print("   Arg 2: quality=LOSSLESS")
    print("\n4. Download with config change:")
    print("   Arg 1: https://tidal.com/browse/track/12345678")
    print("   Arg 2: quality=HI_RES")
    print("\n5. Use password authentication:")
    print("   Arg 3: your_ssh_password")

def main():
    # Parse arguments
    arg1 = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    arg2 = sys.argv[2].strip() if len(sys.argv) > 2 else ""
    arg3 = sys.argv[3].strip() if len(sys.argv) > 3 else ""
    
    # Use arg3 as password if provided
    password = arg3 if arg3 else None
    
    print_header()
    
    # Test connection
    print_colored("🔌 Testing connection...", Colors.YELLOW)
    stdout, stderr, exit_code = execute_ssh_command("echo 'OK'", password)
    
    if exit_code != 0:
        print_colored("❌ Connection failed!", Colors.RED)
        print_colored(f"Error: {stderr}", Colors.RED)
        
        if "Permission denied" in stderr or "Host key verification failed" in stderr:
            print_colored("\n💡 Tips:", Colors.YELLOW)
            print("- Check SSH credentials and key setup")
            print("- Try providing password as 3rd argument")
            print("- Ensure SSH key authentication is configured")
        
        sys.exit(1)
    
    print_colored("✅ Connected successfully!\n", Colors.GREEN)
    
    # Handle different modes
    if not arg1 or arg1.lower() == "help":
        show_help()
        
    elif arg1.lower() == "config":
        if arg2 and "=" in arg2:
            # Set configuration
            key, value = arg2.split("=", 1)
            set_tidal_config(key.strip(), value.strip(), password)
        
        # Always show config after setting
        print_colored("\n📋 Current Configuration:", Colors.CYAN, bold=True)
        config = get_tidal_config(password)
        if config:
            display_config(config)
        else:
            print_colored("No configuration found", Colors.YELLOW)
    
    else:
        # Download mode
        if arg2 and "=" in arg2:
            # Set config before download
            key, value = arg2.split("=", 1)
            print_colored(f"⚙️  Setting {key} = {value} before download", Colors.BLUE)
            set_tidal_config(key.strip(), value.strip(), password)
        
        # Download the content
        success = download_tidal_content(arg1, password)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  Operation cancelled by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
        sys.exit(1)