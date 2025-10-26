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
    
    This tool provides two modes of operation:
    
    \b
    1. Interactive mode: Guided prompts for manual event creation
    2. Bulk mode: Process CSV files with multiple events
    
    Configuration is loaded from environment variables (.env file).
    See .env.example for required configuration.
    
    Examples:
    
    \b
        # Interactive mode
        python main.py interactive
        
        # Bulk upload from CSV
        python main.py bulk events.csv
        
        # Validate CSV without uploading
        python main.py bulk events.csv --dry-run
        
        # Use custom .env file
        python main.py --env-file /path/to/.env interactive
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
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
    console.print("  • [cyan]attack_type[/cyan] - Attack type (direct-flood, amplification, both)")
    console.print("  • [cyan]attacker_ips[/cyan] - Attacker IPs (semicolon-separated)")
    console.print("  • [cyan]victim_ip[/cyan] - Victim IP address")
    console.print("  • [cyan]victim_port[/cyan] - Victim port number")
    console.print("  • [cyan]description[/cyan] - Detailed attack description\n")
    
    console.print("[bold]Optional Fields:[/bold]")
    console.print("  • [cyan]tlp[/cyan] - TLP level (clear, green, amber, red) [default: green]")
    console.print("  • [cyan]workflow_state[/cyan] - Workflow state (new, in-progress, reviewed, closed) [default: new]")
    console.print("  • [cyan]attacker_ports[/cyan] - Attacker ports (semicolon-separated)")
    console.print("  • [cyan]confidence_level[/cyan] - Confidence (high, medium, low) [default: high]\n")
    
    console.print("[bold]Example Row:[/bold]")
    console.print(
        "[dim]2024-01-15,DDoS Attack on Web Server,green,new,direct-flood,"
        "192.168.1.100;192.168.1.101,80;443,10.0.0.50,443,"
        "Large-scale DDoS attack,high[/dim]\n"
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


if __name__ == "__main__":
    cli(obj={})
