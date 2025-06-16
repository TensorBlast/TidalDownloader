#!/usr/bin/env python3
"""
Tidal Downloader - SSH-based tidal-dl-ng wrapper
Downloads Tidal tracks, albums, and playlists via SSH to a remote server
"""

import sys
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import click
import paramiko
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import logging


console = Console()


def parse_tidal_url(url: str) -> Tuple[str, str]:
    """
    Extract type and ID from Tidal URL
    
    This function parses various Tidal URL formats to determine:
    1. What type of content it is (track, album, playlist, video, artist)
    2. The unique ID of that content
    
    It handles URLs like:
    - https://tidal.com/browse/track/46755209
    - https://tidal.com/track/46755209
    - https://tidal.com/browse/album/123456
    - https://tidal.com/browse/playlist/abc-def-ghi
    - Or just a plain numeric ID (assumes it's a track)
    
    Returns:
        Tuple of (media_type, media_id)
    """
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
    
    # Try direct ID format
    if url.isdigit():
        return 'track', url
    
    raise ValueError(f"Could not parse Tidal URL: {url}")


def create_ssh_client(host: str, username: str, port: int = 22, 
                     key_path: Optional[str] = None, password: Optional[str] = None) -> paramiko.SSHClient:
    """Create and configure SSH client"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if key_path:
            key = paramiko.RSAKey.from_private_key_file(Path(key_path).expanduser())
            client.connect(host, port=port, username=username, pkey=key)
        elif password:
            client.connect(host, port=port, username=username, password=password)
        else:
            # Try SSH agent or default key locations first
            try:
                client.connect(host, port=port, username=username)
            except paramiko.AuthenticationException:
                # If key auth fails, prompt for password
                import getpass
                password = getpass.getpass(f"Password for {username}@{host}: ")
                client.connect(host, port=port, username=username, password=password)
        
        return client
    except Exception as e:
        console.print(f"[red]Failed to connect to {host}: {e}[/red]")
        raise


def execute_remote_command(client: paramiko.SSHClient, command: str) -> Tuple[str, str, int]:
    """Execute command on remote server and return output"""
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    return stdout.read().decode(), stderr.read().decode(), exit_status


def get_tidal_config(client: paramiko.SSHClient) -> Dict[str, Any]:
    """Retrieve current tidal-dl-ng configuration from settings.json"""
    import json
    
    # Get the remote user's home directory
    stdout, stderr, exit_status = execute_remote_command(client, "echo $HOME")
    if exit_status != 0:
        console.print(f"[red]Failed to get home directory: {stderr}[/red]")
        return {}
    
    home_dir = stdout.strip()
    config_path = f"{home_dir}/.config/tidal_dl_ng/settings.json"
    
    # Read the settings file
    stdout, stderr, exit_status = execute_remote_command(client, f"cat '{config_path}'")
    
    if exit_status != 0:
        console.print(f"[red]Failed to read config file: {stderr}[/red]")
        console.print(f"[yellow]Config file may not exist at: {config_path}[/yellow]")
        return {}
    
    try:
        config = json.loads(stdout)
        return config
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse config JSON: {e}[/red]")
        return {}


def set_tidal_config(client: paramiko.SSHClient, key: str, value: str) -> bool:
    """Set a tidal-dl-ng configuration option"""
    command = f'tidal-dl-ng cfg "{key}" "{value}"'
    stdout, stderr, exit_status = execute_remote_command(client, command)
    
    if exit_status != 0:
        console.print(f"[red]Failed to set {key}: {stderr}[/red]")
        return False
    
    console.print(f"[green]Set {key} = {value}[/green]")
    return True


def download_tidal_content(client: paramiko.SSHClient, url: str, 
                          show_progress: bool = True) -> bool:
    """Download Tidal content using tidal-dl-ng"""
    command = f'tidal-dl-ng dl "{url}"'
    
    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Downloading from Tidal...", total=None)
            
            stdin, stdout, stderr = client.exec_command(command)
            
            # Stream output in real-time
            while True:
                line = stdout.readline()
                if not line:
                    break
                console.print(line.strip())
            
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode()
                console.print(f"[red]Download failed: {error_output}[/red]")
                return False
    else:
        stdout, stderr, exit_status = execute_remote_command(client, command)
        
        if exit_status != 0:
            console.print(f"[red]Download failed: {stderr}[/red]")
            return False
        
        console.print(stdout)
    
    return True


def display_config(config: Dict[str, Any]):
    """Display configuration in a formatted table"""
    table = Table(title="Current tidal-dl-ng Configuration")
    table.add_column("Option", style="cyan")
    table.add_column("Value", style="green")
    
    def flatten_dict(d: Dict[str, Any], parent_key: str = '') -> Dict[str, str]:
        """Flatten nested dictionary for display"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key).items())
            else:
                items.append((new_key, str(v)))
        return dict(items)
    
    flat_config = flatten_dict(config)
    for key, value in sorted(flat_config.items()):
        table.add_row(key, value)
    
    console.print(table)


@click.command()
@click.argument('server')
@click.argument('tidal_url', required=False)
@click.option('-u', '--username', default=None, help='SSH username (defaults to current user)')
@click.option('-p', '--port', default=22, help='SSH port (default: 22)')
@click.option('-k', '--key', default=None, help='Path to SSH private key')
@click.option('-w', '--password', default=None, help='SSH password (will prompt if not provided and no key auth)')
@click.option('-c', '--config', multiple=True, nargs=2, 
              help='Set tidal-dl-ng config option (can be used multiple times)')
@click.option('--show-config', is_flag=True, help='Show current configuration before downloading')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
def main(server: str, tidal_url: Optional[str], username: Optional[str], port: int,
         key: Optional[str], password: Optional[str], config: List[Tuple[str, str]], 
         show_config: bool, dry_run: bool):
    """Download Tidal content via SSH using tidal-dl-ng on remote server
    
    SERVER: SSH server hostname or IP address
    TIDAL_URL: Tidal URL or ID to download (optional if using --show-config or -c)
    
    Examples:
        # Download a track
        python main.py myserver.com https://tidal.com/browse/track/46755209
        
        # Just show configuration
        python main.py myserver.com --show-config
        
        # Only modify configuration without downloading
        python main.py myserver.com -c quality LOSSLESS -c download_path /music
    """
    
    # Use current username if not specified
    if not username:
        import getpass
        username = getpass.getuser()
    
    # Check if tidal_url is required
    if not tidal_url and not (show_config or config):
        console.print("[red]Error: TIDAL_URL is required unless using --show-config or -c options[/red]")
        sys.exit(1)
    
    try:
        # Parse Tidal URL if provided
        if tidal_url:
            media_type, media_id = parse_tidal_url(tidal_url)
            console.print(f"[cyan]Detected {media_type} with ID: {media_id}[/cyan]")
        
        # Connect to SSH server
        console.print(f"[yellow]Connecting to {username}@{server}:{port}...[/yellow]")
        client = create_ssh_client(server, username, port, key, password)
        console.print("[green]Connected successfully![/green]")
        
        # Apply configuration changes if any
        if config:
            console.print("\n[yellow]Applying configuration changes...[/yellow]")
            for key_name, value in config:
                if not dry_run:
                    set_tidal_config(client, key_name, value)
                else:
                    console.print(f"[dim]Would set {key_name} = {value}[/dim]")
        
        # Show current configuration if requested
        if show_config:
            console.print("\n[yellow]Fetching current configuration...[/yellow]")
            current_config = get_tidal_config(client)
            if current_config:
                display_config(current_config)
        
        # Download content only if URL was provided
        if tidal_url:
            if not dry_run:
                console.print(f"\n[yellow]Starting download of {media_type}...[/yellow]")
                success = download_tidal_content(client, tidal_url)
                
                if success:
                    console.print("\n[green]Download completed successfully![/green]")
                else:
                    console.print("\n[red]Download failed![/red]")
                    sys.exit(1)
            else:
                console.print(f"\n[dim]Would download: {tidal_url}[/dim]")
        elif not show_config and not config:
            console.print("\n[yellow]No action performed. Use --show-config or -c to view/modify configuration.[/yellow]")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    main()
