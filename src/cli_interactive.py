"""
Interactive CLI Module

Provides guided interactive interface for manual MISP DDoS event creation.
Implements user-friendly prompts with validation and helpful feedback.
"""

import logging
from typing import List, Optional
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .misp_client import MISPClient, MISPValidationError, MISPConnectionError

logger = logging.getLogger(__name__)
console = Console()


class InteractiveCLI:
    """
    Interactive command-line interface for creating MISP DDoS events.
    
    Features:
    - Guided prompts with validation
    - Helpful hints and examples
    - Input validation with retry
    - Rich formatted output
    """
    
    def __init__(self, misp_client: MISPClient):
        """
        Initialize interactive CLI.
        
        Args:
            misp_client: Configured MISP client instance
        """
        if not isinstance(misp_client, MISPClient):
            raise TypeError("misp_client must be a MISPClient instance")
        
        self.client = misp_client
        self.console = Console()
    
    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(ip.strip())
            return True
        except ValueError:
            return False
    
    def _validate_port(self, port_str: str) -> bool:
        """Validate port number."""
        try:
            port = int(port_str)
            return 1 <= port <= 65535
        except (ValueError, TypeError):
            return False
    
    def _validate_date(self, date_str: str) -> bool:
        """Validate date format."""
        date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
        for fmt in date_formats:
            try:
                datetime.strptime(date_str.strip(), fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _prompt_with_validation(
        self,
        message: str,
        validator,
        error_message: str,
        default: Optional[str] = None,
        allow_empty: bool = False
    ) -> str:
        """
        Prompt user with validation and retry logic.
        
        Args:
            message: Prompt message
            validator: Validation function returning bool
            error_message: Error message to display on validation failure
            default: Default value
            allow_empty: Allow empty input
        
        Returns:
            Validated user input
        """
        while True:
            value = Prompt.ask(message, default=default)
            
            if allow_empty and not value:
                return value
            
            if not value:
                self.console.print(f"[red]❌ Input cannot be empty[/red]")
                continue
            
            if validator(value):
                return value
            else:
                self.console.print(f"[red]❌ {error_message}[/red]")
    
    def display_welcome(self) -> None:
        """Display welcome banner."""
        welcome_text = """
[bold cyan]MISP DDoS Event Creator[/bold cyan]
[dim]Interactive mode for creating DDoS events following the Streamlined MISP DDoS Playbook[/dim]

This tool will guide you through creating a properly structured DDoS event with:
• Mandatory global tags (TLP, incident type)
• MITRE ATT&CK patterns
• Structured objects (ip-port, annotation)
• Automatic workflow state (new)
        """
        self.console.print(Panel(welcome_text, border_style="cyan"))
    
    def prompt_event_details(self) -> dict:
        """
        Prompt user for all event details with validation.
        
        Returns:
            Dictionary containing all validated event data
        """
        self.console.print("\n[bold]📋 Event Information[/bold]\n")
        
        # Event name
        event_name = self._prompt_with_validation(
            "[cyan]Event name/title[/cyan]",
            lambda x: len(x.strip()) > 0 and len(x.strip()) <= 255,
            "Event name must be 1-255 characters",
        )
        
        # Event date
        self.console.print("\n[dim]Date format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS[/dim]")
        today = datetime.now().strftime("%Y-%m-%d")
        event_date = self._prompt_with_validation(
            "[cyan]Event date[/cyan]",
            self._validate_date,
            "Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS",
            default=today
        )
        
        # Annotation text
        self.console.print("\n[dim]Provide annotation text with detailed information about the DDoS attack[/dim]")
        annotation_text = self._prompt_with_validation(
            "[cyan]Annotation text[/cyan]",
            lambda x: len(x.strip()) > 0 and len(x.strip()) <= 5000,
            "Annotation text must be 1-5000 characters"
        )
        
        # Destination IP information
        self.console.print("\n[bold]🎯 Destination IP Information[/bold]\n")
        self.console.print("[dim]Enter destination IPs being targeted (you'll be prompted for multiple)[/dim]\n")
        
        destination_ips = []
        while True:
            ip = self._prompt_with_validation(
                f"[cyan]Destination IP #{len(destination_ips) + 1}[/cyan] [dim](press Enter when done)[/dim]",
                lambda x: not x or self._validate_ip(x),
                "Invalid IP address format",
                allow_empty=True
            )
            
            if not ip:
                if len(destination_ips) == 0:
                    self.console.print("[yellow]⚠️  At least one destination IP is required[/yellow]")
                    continue
                break
            
            destination_ips.append(ip)
            self.console.print(f"[green]✓ Added {ip}[/green]")
            
            if len(destination_ips) >= 1000:
                self.console.print("[yellow]⚠️  Maximum 1000 IPs reached[/yellow]")
                break
        
        # Destination ports are not collected (not typically available)
        destination_ports = None
        
        # TLP Level
        self.console.print("\n[bold]🏷️  Metadata[/bold]\n")
        self.console.print("[dim]TLP (Traffic Light Protocol) levels:[/dim]")
        self.console.print("  1. [green]clear[/green] - Public information")
        self.console.print("  2. [green]green[/green] - Community sharing (default)")
        self.console.print("  3. [yellow]amber[/yellow] - Limited sharing")
        self.console.print("  4. [red]red[/red] - No sharing\n")
        
        tlp_map = {"1": "clear", "2": "green", "3": "amber", "4": "red"}
        tlp_choice = self._prompt_with_validation(
            "[cyan]Select TLP level[/cyan] [dim](1-4)[/dim]",
            lambda x: x in tlp_map,
            "Please enter 1, 2, 3, or 4",
            default="2"
        )
        tlp = tlp_map[tlp_choice]
        
        # Workflow state is always "new" - SOC analysts will update during peer review
        workflow_state = "new"
        
        return {
            "event_name": event_name,
            "event_date": event_date,
            "annotation_text": annotation_text,
            "destination_ips": destination_ips,
            "destination_ports": destination_ports if destination_ports else None,
            "tlp": tlp,
            "workflow_state": workflow_state
        }
    
    def display_summary(self, event_data: dict) -> None:
        """
        Display summary of event data for confirmation.
        
        Args:
            event_data: Dictionary containing event details
        """
        self.console.print("\n[bold]📊 Event Summary[/bold]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Event Name", event_data["event_name"])
        table.add_row("Date", event_data["event_date"])
        table.add_row("Destination IPs", f"{len(event_data['destination_ips'])} IP(s)")
        table.add_row("TLP Level", event_data["tlp"])
        table.add_row("Workflow State", "new")  # Always "new" - SOC analysts update during peer review
        table.add_row("Annotation", event_data["annotation_text"][:100] + "..." if len(event_data["annotation_text"]) > 100 else event_data["annotation_text"])
        
        self.console.print(table)
    
    def run(self) -> Optional[dict]:
        """
        Run the interactive CLI session.
        
        Returns:
            Dictionary with event creation result, or None if cancelled
        """
        try:
            self.display_welcome()
            
            # Collect event details
            event_data = self.prompt_event_details()
            
            # Display summary
            self.display_summary(event_data)
            
            # Confirm submission
            self.console.print()
            confirm = Confirm.ask(
                "[bold cyan]Submit this event to MISP?[/bold cyan]",
                default=True
            )
            
            if not confirm:
                self.console.print("\n[yellow]❌ Event creation cancelled[/yellow]")
                return None
            
            # Create event
            self.console.print("\n[cyan]📤 Creating event in MISP...[/cyan]")
            
            result = self.client.create_ddos_event(**event_data)
            
            # Display success
            self.console.print("\n[bold green]✅ Event created successfully![/bold green]\n")
            
            success_table = Table(show_header=False, box=None)
            success_table.add_column("Field", style="cyan")
            success_table.add_column("Value", style="green")
            
            success_table.add_row("Event ID", str(result["event_id"]))
            success_table.add_row("Event UUID", result["event_uuid"])
            success_table.add_row("Event URL", result["url"])
            
            self.console.print(success_table)
            
            return result
            
        except MISPValidationError as e:
            self.console.print(f"\n[bold red]❌ Validation Error:[/bold red]")
            self.console.print(f"[red]{str(e)}[/red]")
            logger.error(f"Validation error: {e}")
            return None
            
        except MISPConnectionError as e:
            self.console.print(f"\n[bold red]❌ Connection Error:[/bold red]")
            self.console.print(f"[red]{str(e)}[/red]")
            self.console.print("[yellow]Please check your MISP connection and try again.[/yellow]")
            logger.error(f"Connection error: {e}")
            return None
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            return None
            
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Unexpected Error:[/bold red]")
            self.console.print(f"[red]{str(e)}[/red]")
            logger.exception("Unexpected error in interactive CLI")
            return None
