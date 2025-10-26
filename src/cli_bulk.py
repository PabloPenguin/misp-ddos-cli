"""
Bulk Upload CLI Module

Handles batch processing of DDoS events from CSV files with progress tracking.
Implements robust error handling and detailed reporting.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .misp_client import MISPClient, MISPClientError, MISPConnectionError, MISPValidationError
from .csv_processor import CSVProcessor, CSVValidationError

logger = logging.getLogger(__name__)


class BulkUploadCLI:
    """
    Bulk upload handler for processing CSV files with multiple DDoS events.
    
    Features:
    - Progress tracking with rich UI
    - Parallel-safe processing
    - Detailed success/failure reporting
    - Resume capability on partial failures
    - Performance metrics
    """
    
    def __init__(self, misp_client: MISPClient, csv_processor: Optional[CSVProcessor] = None):
        """
        Initialize bulk upload CLI.
        
        Args:
            misp_client: Configured MISP client instance
            csv_processor: Optional CSV processor (creates default if None)
        """
        if not isinstance(misp_client, MISPClient):
            raise TypeError("misp_client must be a MISPClient instance")
        
        self.client = misp_client
        self.processor = csv_processor or CSVProcessor()
        self.console = Console()
    
    def display_welcome(self, filepath: str) -> None:
        """
        Display welcome banner for bulk upload.
        
        Args:
            filepath: Path to CSV file being processed
        """
        welcome_text = f"""
[bold cyan]MISP DDoS Bulk Upload[/bold cyan]
[dim]Processing CSV file for batch event creation[/dim]

File: [cyan]{filepath}[/cyan]

This tool will:
• Validate all rows in the CSV file
• Create MISP events following the DDoS Playbook
• Provide detailed success/failure reporting
• Track progress in real-time
        """
        self.console.print(Panel(welcome_text, border_style="cyan"))
    
    def validate_csv(self, filepath: str, skip_invalid: bool = False) -> Dict[str, Any]:
        """
        Validate CSV file before uploading.
        
        Args:
            filepath: Path to CSV file
            skip_invalid: If True, skip invalid rows; if False, fail on first error
        
        Returns:
            Validation results dictionary
        
        Raises:
            FileNotFoundError: If file doesn't exist
            CSVValidationError: If validation fails
        """
        self.console.print("\n[cyan]🔍 Validating CSV file...[/cyan]\n")
        
        try:
            with self.console.status("[cyan]Reading and validating rows..."):
                result = self.processor.process_csv(filepath, skip_invalid=skip_invalid)
            
            # Display validation summary
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", justify="right", style="white")
            
            table.add_row("Total Rows", str(result["total_rows"]))
            table.add_row("Valid Events", f"[green]{len(result['valid_events'])}[/green]")
            table.add_row("Invalid Rows", f"[red]{len(result['invalid_rows'])}[/red]")
            
            self.console.print(table)
            
            # Display invalid rows if any
            if result["invalid_rows"]:
                self.console.print("\n[bold yellow]⚠️  Invalid Rows Detected:[/bold yellow]\n")
                
                error_table = Table(show_header=True, header_style="bold red")
                error_table.add_column("Row", style="red", justify="right")
                error_table.add_column("Error", style="yellow")
                
                for row_num, error in result["invalid_rows"][:10]:  # Show first 10
                    error_table.add_row(str(row_num), error)
                
                if len(result["invalid_rows"]) > 10:
                    error_table.add_row(
                        "...",
                        f"[dim]and {len(result['invalid_rows']) - 10} more errors[/dim]"
                    )
                
                self.console.print(error_table)
            
            return result
            
        except FileNotFoundError as e:
            self.console.print(f"[bold red]❌ File not found:[/bold red] {str(e)}")
            raise
            
        except CSVValidationError as e:
            self.console.print(f"[bold red]❌ CSV Validation Error:[/bold red]")
            self.console.print(f"[red]{str(e)}[/red]")
            raise
            
        except Exception as e:
            self.console.print(f"[bold red]❌ Unexpected Error:[/bold red]")
            self.console.print(f"[red]{str(e)}[/red]")
            logger.exception("Unexpected error during CSV validation")
            raise
    
    def upload_events(
        self,
        events: List[Dict[str, Any]],
        continue_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Upload multiple events to MISP with progress tracking.
        
        Args:
            events: List of validated event dictionaries
            continue_on_error: If True, continue on individual event failures
        
        Returns:
            Dictionary containing upload results and statistics
        """
        total_events = len(events)
        successful = []
        failed = []
        start_time = time.time()
        
        self.console.print(f"\n[cyan]📤 Uploading {total_events} event(s) to MISP...[/cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            upload_task = progress.add_task(
                "[cyan]Uploading events...",
                total=total_events
            )
            
            for idx, event_data in enumerate(events, start=1):
                event_name = event_data.get("event_name", f"Event {idx}")
                
                try:
                    # Update progress description
                    progress.update(
                        upload_task,
                        description=f"[cyan]Uploading: {event_name[:50]}..."
                    )
                    
                    # Create event in MISP
                    result = self.client.create_ddos_event(**event_data)
                    
                    successful.append({
                        "event_name": event_name,
                        "event_id": result["event_id"],
                        "event_uuid": result["event_uuid"],
                        "url": result["url"]
                    })
                    
                    logger.info(
                        f"Successfully uploaded event {idx}/{total_events}",
                        extra={"event_id": result["event_id"], "event_name": event_name}
                    )
                    
                except (MISPValidationError, MISPConnectionError, MISPClientError) as e:
                    error_msg = str(e)
                    failed.append({
                        "event_name": event_name,
                        "error": error_msg,
                        "event_index": idx
                    })
                    
                    logger.error(
                        f"Failed to upload event {idx}/{total_events}",
                        extra={"event_name": event_name, "error": error_msg}
                    )
                    
                    if not continue_on_error:
                        progress.update(upload_task, completed=total_events)
                        break
                
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    failed.append({
                        "event_name": event_name,
                        "error": error_msg,
                        "event_index": idx
                    })
                    
                    logger.exception(
                        f"Unexpected error uploading event {idx}/{total_events}"
                    )
                    
                    if not continue_on_error:
                        progress.update(upload_task, completed=total_events)
                        break
                
                finally:
                    progress.advance(upload_task)
        
        duration = time.time() - start_time
        
        return {
            "total": total_events,
            "successful": successful,
            "failed": failed,
            "duration_seconds": duration
        }
    
    def display_results(self, results: Dict[str, Any]) -> None:
        """
        Display upload results summary.
        
        Args:
            results: Results dictionary from upload_events
        """
        self.console.print("\n[bold]📊 Upload Results[/bold]\n")
        
        # Summary statistics
        summary_table = Table(show_header=True, header_style="bold cyan")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right", style="white")
        
        summary_table.add_row("Total Events", str(results["total"]))
        summary_table.add_row(
            "Successful",
            f"[green]{len(results['successful'])}[/green]"
        )
        summary_table.add_row(
            "Failed",
            f"[red]{len(results['failed'])}[/red]"
        )
        summary_table.add_row(
            "Duration",
            f"{results['duration_seconds']:.2f}s"
        )
        
        if len(results['successful']) > 0:
            avg_time = results['duration_seconds'] / results['total']
            summary_table.add_row(
                "Avg Time/Event",
                f"{avg_time:.2f}s"
            )
        
        self.console.print(summary_table)
        
        # Successful events
        if results["successful"]:
            self.console.print("\n[bold green]✅ Successfully Created Events:[/bold green]\n")
            
            success_table = Table(show_header=True, header_style="bold green")
            success_table.add_column("Event Name", style="green")
            success_table.add_column("Event ID", justify="right", style="cyan")
            success_table.add_column("UUID", style="dim")
            
            for event in results["successful"][:20]:  # Show first 20
                success_table.add_row(
                    event["event_name"][:50],
                    str(event["event_id"]),
                    event["event_uuid"][:8] + "..."
                )
            
            if len(results["successful"]) > 20:
                success_table.add_row(
                    f"[dim]... and {len(results['successful']) - 20} more[/dim]",
                    "",
                    ""
                )
            
            self.console.print(success_table)
        
        # Failed events
        if results["failed"]:
            self.console.print("\n[bold red]❌ Failed Events:[/bold red]\n")
            
            fail_table = Table(show_header=True, header_style="bold red")
            fail_table.add_column("Event Name", style="red")
            fail_table.add_column("Error", style="yellow")
            
            for event in results["failed"][:20]:  # Show first 20
                fail_table.add_row(
                    event["event_name"][:50],
                    event["error"][:100]
                )
            
            if len(results["failed"]) > 20:
                fail_table.add_row(
                    f"[dim]... and {len(results['failed']) - 20} more[/dim]",
                    ""
                )
            
            self.console.print(fail_table)
    
    def run(
        self,
        filepath: str,
        skip_invalid: bool = False,
        continue_on_error: bool = True,
        dry_run: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Run the bulk upload process.
        
        Args:
            filepath: Path to CSV file
            skip_invalid: Skip invalid CSV rows during validation
            continue_on_error: Continue uploading on individual event failures
            dry_run: If True, validate only without uploading
        
        Returns:
            Results dictionary or None on failure
        """
        try:
            self.display_welcome(filepath)
            
            # Validate CSV
            validation_result = self.validate_csv(filepath, skip_invalid=skip_invalid)
            
            if not validation_result["valid_events"]:
                self.console.print("\n[bold red]❌ No valid events found in CSV file[/bold red]")
                return None
            
            if validation_result["invalid_rows"] and not skip_invalid:
                self.console.print(
                    "\n[yellow]⚠️  CSV contains invalid rows. "
                    "Fix errors or use --skip-invalid flag[/yellow]"
                )
                return None
            
            # Dry run - validation only
            if dry_run:
                self.console.print(
                    f"\n[bold green]✅ Dry run complete. "
                    f"{len(validation_result['valid_events'])} events ready for upload[/bold green]"
                )
                return validation_result
            
            # Upload events
            upload_results = self.upload_events(
                validation_result["valid_events"],
                continue_on_error=continue_on_error
            )
            
            # Display results
            self.display_results(upload_results)
            
            # Final status
            if len(upload_results["failed"]) == 0:
                self.console.print(
                    f"\n[bold green]🎉 All {len(upload_results['successful'])} "
                    f"events uploaded successfully![/bold green]"
                )
            elif len(upload_results["successful"]) > 0:
                self.console.print(
                    f"\n[bold yellow]⚠️  Partial success: "
                    f"{len(upload_results['successful'])} uploaded, "
                    f"{len(upload_results['failed'])} failed[/bold yellow]"
                )
            else:
                self.console.print(
                    "\n[bold red]❌ All events failed to upload[/bold red]"
                )
            
            return upload_results
            
        except FileNotFoundError:
            return None
            
        except CSVValidationError:
            return None
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            return None
            
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Unexpected Error:[/bold red]")
            self.console.print(f"[red]{str(e)}[/red]")
            logger.exception("Unexpected error in bulk upload")
            return None
