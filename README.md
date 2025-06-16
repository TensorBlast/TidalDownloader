# Tidal Downloader

A Python-based tool that uses SSH to download Tidal tracks, albums, playlists, and videos via `tidal-dl-ng` on a remote server. Features both command-line and Raycast integration for seamless workflow automation.

## Overview

This project provides two ways to interact with a remote `tidal-dl-ng` installation:

1. **Command-line tool** (`main.py`) - Full-featured CLI with comprehensive options
2. **Raycast script** (`tidal-downloader.py`) - Streamlined interface for quick downloads

Both tools connect to a remote server via SSH and execute `tidal-dl-ng` commands, allowing you to download Tidal content without installing the downloader locally.

## Prerequisites

- **Remote server** with `tidal-dl-ng` installed and configured
- **SSH access** to the server (key-based or password authentication)
- **Python 3.13+** (as specified in `.python-version`)
- **uv** package manager for dependency management

## Installation

1. Clone or download this repository
2. Install dependencies using uv:
   ```bash
   uv sync
   ```

## Configuration

### Server Setup
- Default server: `192.168.77.247`
- SSH port: `22` 
- Authentication: SSH keys (preferred) or password

### Remote Server Requirements
- `tidal-dl-ng` must be installed and configured
- Valid Tidal subscription and login on the server
- Configuration file location: `~/.config/tidal_dl_ng/settings.json`

## Usage

### Command Line Tool (`main.py`)

**Basic download:**
```bash
uv run main.py 192.168.77.247 https://tidal.com/browse/track/46755209
```

**With SSH options:**
```bash
uv run main.py 192.168.77.247 https://tidal.com/browse/track/46755209 -u username -k ~/.ssh/id_rsa
```

**Configuration management:**
```bash
# Show current configuration
uv run main.py 192.168.77.247 --show-config

# Set configuration options
uv run main.py 192.168.77.247 -c quality LOSSLESS -c download_path /music/tidal

# Modify config without downloading
uv run main.py 192.168.77.247 -c quality HI_RES --show-config
```

**Available options:**
- `-u, --username` - SSH username (defaults to current user)
- `-p, --port` - SSH port (default: 22)
- `-k, --key` - Path to SSH private key
- `-w, --password` - SSH password (will prompt if needed)
- `-c, --config` - Set config option (format: key value)
- `--show-config` - Display current configuration
- `--dry-run` - Preview actions without executing

### Raycast Integration (`tidal-downloader.py`)

The Raycast script provides a streamlined interface optimized for quick access.

**Setup:**
1. Copy the script to your Raycast scripts directory:
   ```bash
   cp tidal-downloader.py ~/Documents/Raycast\ Scripts/
   ```
2. Make sure it's executable (already done)
3. Open Raycast and search for "Tidal Downloader"

**Usage modes:**

1. **Simple Download:**
   - Arg 1: `https://tidal.com/browse/track/46755209`

2. **Show Configuration:**
   - Arg 1: `config`

3. **Set Configuration:**
   - Arg 1: `config`
   - Arg 2: `quality=LOSSLESS`

4. **Download with Config:**
   - Arg 1: `https://tidal.com/browse/track/46755209`
   - Arg 2: `quality=HI_RES`

5. **With Password:**
   - Arg 1: (URL or config)
   - Arg 2: (optional config)
   - Arg 3: `your_password`

## Supported Tidal Content

The tool supports all major Tidal content types:

- **Tracks**: `https://tidal.com/browse/track/12345678`
- **Albums**: `https://tidal.com/browse/album/12345678`
- **Playlists**: `https://tidal.com/browse/playlist/abc-def-ghi`
- **Videos**: `https://tidal.com/browse/video/12345678`
- **Artists**: `https://tidal.com/browse/artist/12345678` (downloads all artist content)
- **Direct IDs**: Just the numeric ID (assumes track)

## Common Configuration Options

Popular `tidal-dl-ng` configuration options you can modify:

- `quality` - Audio quality (NORMAL, HIGH, HI_RES, LOSSLESS)
- `download_path` - Download directory path
- `album_folder_format` - Album folder naming
- `track_file_format` - Track file naming
- `include_lyrics` - Include lyrics files
- `include_covers` - Include album artwork

## Authentication

### SSH Key Authentication (Recommended)
```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy public key to server
ssh-copy-id user@192.168.77.247

# Test connection
ssh user@192.168.77.247 "echo 'Connection successful'"
```

### Password Authentication
The tools support password authentication as a fallback:
- Command-line: Use `-w password` or will prompt if key auth fails
- Raycast: Provide password as the 3rd argument

## Development

### Project Structure
- `main.py` - Full-featured command-line interface
- `tidal-downloader.py` - Raycast script for quick access
- `pyproject.toml` - Project dependencies and metadata
- `CLAUDE.md` - Development guidelines and conventions

### Dependencies
- `paramiko` - SSH connection handling
- `click` - Command-line interface framework
- `rich` - Enhanced terminal output and formatting

### Development Commands
```bash
# Install dependencies
uv sync

# Run the application
uv run main.py

# Add new dependencies
uv add package-name
```

## Troubleshooting

### Connection Issues
- Verify SSH server is accessible: `ssh user@192.168.77.247`
- Check SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
- Ensure server has `tidal-dl-ng` installed: `ssh user@server "which tidal-dl-ng"`

### Download Issues
- Verify Tidal login on server: `ssh user@server "tidal-dl-ng login"`
- Check available disk space on server
- Ensure proper permissions in download directory

### Configuration Issues
- Configuration file location: `~/.config/tidal_dl_ng/settings.json`
- Reset config: `ssh user@server "rm ~/.config/tidal_dl_ng/settings.json"`
- Manual config: `ssh user@server "tidal-dl-ng cfg"`
