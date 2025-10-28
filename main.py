#!/usr/bin/env python3
"""
MISP DDoS CLI Tool

Command-line interface for creating MISP DDoS events following the
Streamlined MISP DDoS Playbook.

Supports:
- Interactive manual event creation
- Bulk upload from CSV files
- Comprehensive validation and error handling
- Secure communication with MISP instance
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from src.config import Config, ConfigurationError, setup_logging
from src.misp_client import MISPClient, MISPClientError, MISPConnectionError
from src.cli_interactive import InteractiveCLI
from src.cli_bulk import BulkUploadCLI
from src.csv_processor import CSVProcessor
from src.auto_update import auto_update

__version__ = "1.0.0"

console = Console()
logger = logging.getLogger(__name__)


def print_version(ctx, param, value):
    """Print version and exit."""
    if not value or ctx.resilient_parsing:
        return
    console.print(f"[cyan]MISP DDoS CLI v{__version__}[/cyan]")
    ctx.exit()


def print_banner():
    """Print application banner."""
    banner = f"""
[bold cyan]╔═══════════════════════════════════════════════════════════╗
║           MISP DDoS Event Management CLI v{__version__}          ║
║                                                           ║
║  Streamlined DDoS Event Creation for Shared MISP         ║
║  Following MISP DDoS Playbook Best Practices             ║
╚═══════════════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)


@click.group()
@click.option(
    '--version',
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help='Show version and exit'
)
@click.option(
    '--env-file',
    type=click.Path(exists=True),
    help='Path to .env file (default: .env in current directory)'
)
@click.option(
    '--debug',
    is_flag=True,
    help='Enable debug logging'
)
@click.pass_context
def cli(ctx, env_file: Optional[str], debug: bool):
    """
    MISP DDoS CLI - Create and manage DDoS events in MISP.
    
    Automatically checks for updates from GitHub on every run to ensure
    you're using the latest version.
    
    \b
    Available Commands:
    
    \b
    • interactive    - Guided prompts for manual event creation
    • bulk          - Process and upload CSV files with multiple events
    • export        - Export all MISP events to JSON format (SIEM-ready)
    • template      - Display CSV template information and field descriptions
    • test-connection - Test your MISP connection and verify credentials
    
    Configuration is loaded from environment variables (.env file).
    See .env.example for required configuration.
    
    \b
    Quick Start:
    
    \b
        # Test your MISP connection first
        python main.py test-connection
        
        # Create events interactively
        python main.py interactive
        
        # View CSV template info
        python main.py template
        
        # Bulk upload from CSV
        python main.py bulk events.csv
        
        # Export events for SIEM
        python main.py export --pretty
        
        # Validate CSV without uploading
        python main.py bulk events.csv --dry-run
        
        # Use custom .env file
        python main.py --env-file /path/to/.env interactive
        
        # Enable debug logging
        python main.py --debug interactive
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Check for updates from GitHub every time the script runs
    try:
        console.print("[cyan]Checking for updates from GitHub...[/cyan]")
        updated, update_message = auto_update(silent=False)
        if updated:
            console.print(f"[green]SUCCESS: Updated successfully - {update_message}[/green]")
            console.print("[yellow]WARNING: Please restart the script to use the latest version[/yellow]\n")
        else:
            # Show the status even if no update
            if "Already up to date" in update_message:
                console.print(f"[green]OK: {update_message}[/green]\n")
            elif "Git not available" in update_message or "Not a git repository" in update_message:
                console.print(f"[dim]INFO: Auto-update skipped - {update_message}[/dim]\n")
            else:
                console.print(f"[dim]INFO: {update_message}[/dim]\n")
    except Exception as e:
        # Never fail on update check, but inform the user
        console.print(f"[yellow]WARNING: Could not check for updates - {str(e)}[/yellow]\n")
        logger.debug(f"Auto-update check failed: {e}")
    
    try:
        # Load configuration
        config = Config(env_file=env_file)
        
        # Override log level if debug flag set
        if debug:
            config.log_level = "DEBUG"
        
        # Setup logging
        setup_logging(config)
        
        # Store config in context
        ctx.obj['config'] = config
        
        logger.debug("CLI initialized successfully")
        
    except ConfigurationError as e:
        console.print(f"[bold red]❌ Configuration Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]\n")
        console.print("[yellow]Tip: Copy .env.example to .env and fill in your MISP details[/yellow]")
        sys.exit(1)
    
    except Exception as e:
        console.print(f"[bold red]❌ Initialization Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        logger.exception("Failed to initialize CLI")
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """
    Launch interactive mode for manual event creation.
    
    This mode provides a guided interface with prompts for all required
    event information. Input is validated in real-time with helpful hints.
    
    Example:
    
    \b
        python main.py interactive
    """
    try:
        print_banner()
        
        config = ctx.obj['config']
        
        # Initialize MISP client
        logger.info("Connecting to MISP instance...")
        misp_client = MISPClient(
            url=config.misp_url,
            api_key=config.misp_api_key,
            verify_ssl=config.misp_verify_ssl,
            timeout=config.misp_timeout,
            max_retries=config.misp_max_retries
        )
        
        # Run interactive CLI
        interactive_cli = InteractiveCLI(misp_client)
        result = interactive_cli.run()
        
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except MISPConnectionError as e:
        console.print(f"\n[bold red]❌ MISP Connection Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  • Verify MISP_URL is correct in .env")
        console.print("  • Check MISP_API_KEY is valid")
        console.print("  • Ensure MISP instance is accessible")
        console.print("  • Check network/firewall settings")
        sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        logger.exception("Unexpected error in interactive mode")
        sys.exit(1)


@cli.command()
@click.argument(
    'csv_file',
    type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    '--skip-invalid',
    is_flag=True,
    help='Skip invalid rows instead of failing'
)
@click.option(
    '--continue-on-error',
    is_flag=True,
    default=True,
    help='Continue uploading even if some events fail (default: enabled)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Validate CSV without uploading to MISP'
)
@click.pass_context
def bulk(
    ctx,
    csv_file: Path,
    skip_invalid: bool,
    continue_on_error: bool,
    dry_run: bool
):
    """
    Bulk upload DDoS events from CSV file.
    
    The CSV file must follow the template format (see templates/ddos_event_template.csv).
    All rows are validated before upload begins.
    
    \b
    CSV File Format:
        • Required columns: date, event_name, attack_type, attacker_ips, 
          victim_ip, victim_port, description
        • Optional columns: tlp, workflow_state, attacker_ports, confidence_level
        • Use semicolon (;) to separate multiple values in array fields
    
    Examples:
    
    \b
        # Upload events from CSV
        python main.py bulk events.csv
        
        # Validate only (no upload)
        python main.py bulk events.csv --dry-run
        
        # Skip invalid rows
        python main.py bulk events.csv --skip-invalid
        
        # Stop on first error
        python main.py bulk events.csv --no-continue-on-error
    
    Args:
        CSV_FILE: Path to CSV file containing DDoS events
    """
    try:
        print_banner()
        
        config = ctx.obj['config']
        
        # Initialize MISP client
        logger.info("Connecting to MISP instance...")
        misp_client = MISPClient(
            url=config.misp_url,
            api_key=config.misp_api_key,
            verify_ssl=config.misp_verify_ssl,
            timeout=config.misp_timeout,
            max_retries=config.misp_max_retries
        )
        
        # Run bulk upload
        bulk_cli = BulkUploadCLI(misp_client)
        result = bulk_cli.run(
            filepath=str(csv_file),
            skip_invalid=skip_invalid,
            continue_on_error=continue_on_error,
            dry_run=dry_run
        )
        
        if result:
            # Exit with error if there were failures (unless dry run)
            if not dry_run and result.get('failed'):
                sys.exit(1)
            sys.exit(0)
        else:
            sys.exit(1)
    
    except MISPConnectionError as e:
        console.print(f"\n[bold red]❌ MISP Connection Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  • Verify MISP_URL is correct in .env")
        console.print("  • Check MISP_API_KEY is valid")
        console.print("  • Ensure MISP instance is accessible")
        console.print("  • Check network/firewall settings")
        sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        logger.exception("Unexpected error in bulk mode")
        sys.exit(1)


@cli.command()
def template():
    """
    Display information about the CSV template.
    
    Shows the location of the CSV template file and field descriptions.
    """
    console.print("\n[bold cyan]📄 CSV Template Information[/bold cyan]\n")
    
    template_path = Path("templates/ddos_event_template.csv")
    
    if template_path.exists():
        console.print(f"[green]✓ Template file found:[/green] {template_path.absolute()}\n")
    else:
        console.print(f"[yellow]⚠️  Template file not found at expected location:[/yellow] {template_path.absolute()}\n")
    
    console.print("[bold]Required Fields:[/bold]")
    console.print("  • [cyan]date[/cyan] - Event date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)")
    console.print("  • [cyan]event_name[/cyan] - Event title/name")
    console.print("  • [cyan]attacker_ips[/cyan] - Attacker/source IPs launching the attack (semicolon-separated)")
    console.print("  • [cyan]annotation_text[/cyan] - Detailed annotation text about the attack\n")
    
    console.print("[bold]Optional Fields:[/bold]")
    console.print("  • [cyan]tlp[/cyan] - TLP level (clear, green, amber, red) [default: green]")
    console.print("  • [cyan]destination_ips[/cyan] - Destination IPs being targeted (semicolon-separated)")
    console.print("  • [cyan]destination_ports[/cyan] - Destination ports (semicolon-separated)\n")
    
    console.print("[bold]Example Row:[/bold]")
    console.print(
        "[dim]2025-10-28,DDoS Botnet Attack,green,"
        "203.0.113.10;203.0.113.11,,,"
        "Large-scale DDoS attack from known botnet infrastructure[/dim]\n"
    )


@cli.command()
@click.pass_context
def test_connection(ctx):
    """
    Test connection to MISP instance.
    
    Verifies that the MISP instance is accessible with the configured
    credentials and displays connection information.
    """
    try:
        console.print("\n[cyan]Testing MISP connection...[/cyan]\n")
        
        config = ctx.obj['config']
        
        # Display configuration (without sensitive data)
        console.print(f"[dim]MISP URL:[/dim] {config.misp_url}")
        console.print(f"[dim]SSL Verification:[/dim] {config.misp_verify_ssl}")
        console.print(f"[dim]Timeout:[/dim] {config.misp_timeout}s")
        console.print(f"[dim]Max Retries:[/dim] {config.misp_max_retries}\n")
        
        # Test connection
        misp_client = MISPClient(
            url=config.misp_url,
            api_key=config.misp_api_key,
            verify_ssl=config.misp_verify_ssl,
            timeout=config.misp_timeout,
            max_retries=config.misp_max_retries
        )
        
        console.print("[bold green]✅ Connection successful![/bold green]")
        console.print("[dim]MISP instance is accessible and API key is valid[/dim]\n")
        
        sys.exit(0)
    
    except MISPConnectionError as e:
        console.print(f"[bold red]❌ Connection failed:[/bold red]")
        console.print(f"[red]{str(e)}[/red]\n")
        console.print("[yellow]Troubleshooting:[/yellow]")
        console.print("  • Verify MISP_URL is correct")
        console.print("  • Check MISP_API_KEY is valid")
        console.print("  • Ensure MISP instance is running and accessible")
        console.print("  • Check network/firewall settings")
        console.print("  • If using self-hosted with self-signed cert, ensure MISP_VERIFY_SSL=false\n")
        sys.exit(1)
    
    except Exception as e:
        console.print(f"[bold red]❌ Unexpected Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        logger.exception("Error testing connection")
        sys.exit(1)


@cli.command()
@click.option(
    '--output',
    '-o',
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help='Output JSON file path (default: misp_events_export_YYYY-MM-DD_HHMMSS.json)'
)
@click.option(
    '--pretty',
    is_flag=True,
    help='Pretty-print JSON output with indentation'
)
@click.pass_context
def export(ctx, output: Optional[Path], pretty: bool):
    """
    Export all MISP events to JSON format.
    
    Retrieves all events from the MISP instance with complete details including
    all attributes, objects, tags, galaxies, and metadata. The output JSON is
    designed for easy ingestion into SIEM systems and sharing with other organizations.
    
    \b
    Features:
        • Exports ALL events visible to your API key
        • Includes complete event details (attributes, objects, tags, galaxies)
        • SIEM-ready JSON format
        • Optional pretty-printing for human readability
        • Automatic timestamped filename
    
    \b
    Security Notes:
        • Only exports events accessible with your API key permissions
        • Consider filtering by TLP level if sharing externally
        • Review exported data before sharing with other organizations
    
    Examples:
    
    \b
        # Export to timestamped file
        python main.py export
        
        # Export to specific file
        python main.py export -o events.json
        
        # Export with pretty formatting
        python main.py export --pretty
        
        # Custom output with formatting
        python main.py export -o export/misp_events.json --pretty
    """
    try:
        print_banner()
        
        config = ctx.obj['config']
        
        # Generate default filename with timestamp if not provided
        if output is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output = Path(f"misp_events_export_{timestamp}.json")
        
        # Create output directory if it doesn't exist
        output_dir = output.parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        console.print("\n[bold cyan]📥 MISP Event Export[/bold cyan]\n")
        console.print(f"[dim]Output file:[/dim] {output.absolute()}")
        console.print(f"[dim]Pretty print:[/dim] {'Yes' if pretty else 'No'}\n")
        
        # Initialize MISP client
        logger.info("Connecting to MISP instance...")
        console.print("[cyan]🔗 Connecting to MISP instance...[/cyan]")
        
        misp_client = MISPClient(
            url=config.misp_url,
            api_key=config.misp_api_key,
            verify_ssl=config.misp_verify_ssl,
            timeout=config.misp_timeout,
            max_retries=config.misp_max_retries
        )
        
        console.print("[green]✓[/green] Connected successfully\n")
        
        # Export all events
        console.print("[cyan]📤 Exporting all events from MISP...[/cyan]")
        console.print("[dim]This may take a while for large MISP instances...[/dim]\n")
        
        with console.status("[cyan]Fetching events..."):
            events = misp_client.export_all_events()
        
        # Display export statistics
        console.print(f"[green]✓[/green] Successfully retrieved [bold cyan]{len(events)}[/bold cyan] events\n")
        
        # Calculate statistics
        total_attributes = sum(len(event.get('Attribute', [])) for event in events)
        total_objects = sum(len(event.get('Object', [])) for event in events)
        
        from rich.table import Table
        stats_table = Table(show_header=True, header_style="bold cyan")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", justify="right", style="white")
        
        stats_table.add_row("Events", str(len(events)))
        stats_table.add_row("Total Attributes", str(total_attributes))
        stats_table.add_row("Total Objects", str(total_objects))
        
        console.print(stats_table)
        console.print()
        
        # Write to JSON file
        console.print(f"[cyan]💾 Writing to JSON file...[/cyan]")
        
        import json
        
        try:
            with open(output, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(events, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(events, f, ensure_ascii=False)
            
            # Get file size
            file_size = output.stat().st_size
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            
            console.print(f"[green]✓[/green] Export complete!\n")
            console.print(f"[bold green]📄 File saved:[/bold green] {output.absolute()}")
            console.print(f"[dim]File size:[/dim] {size_str}\n")
            
            console.print("[bold cyan]Next Steps:[/bold cyan]")
            console.print("  • Review the exported JSON file")
            console.print("  • Import into your SIEM or analysis platform")
            console.print("  • Share with other organizations as needed")
            console.print("  • Consider filtering by TLP level before sharing\n")
            
            logger.info(
                "Export completed successfully",
                extra={
                    "output_file": str(output.absolute()),
                    "event_count": len(events),
                    "file_size_bytes": file_size
                }
            )
            
            sys.exit(0)
        
        except IOError as e:
            console.print(f"\n[bold red]❌ Failed to write output file:[/bold red]")
            console.print(f"[red]{str(e)}[/red]\n")
            console.print("[yellow]Troubleshooting:[/yellow]")
            console.print("  • Check write permissions for output directory")
            console.print("  • Ensure sufficient disk space")
            console.print("  • Verify output path is valid")
            logger.exception("Failed to write export file")
            sys.exit(1)
    
    except MISPConnectionError as e:
        console.print(f"\n[bold red]❌ MISP Connection Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  • Verify MISP_URL is correct in .env")
        console.print("  • Check MISP_API_KEY is valid")
        console.print("  • Ensure MISP instance is accessible")
        console.print("  • Check network/firewall settings")
        sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Export cancelled by user[/yellow]")
        sys.exit(130)
    
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected Error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        logger.exception("Unexpected error during export")
        sys.exit(1)


if __name__ == "__main__":
    cli(obj={})
