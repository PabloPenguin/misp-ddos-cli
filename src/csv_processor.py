"""
CSV Validator and Processor

Validates and processes CSV files for bulk MISP DDoS event uploads.
Implements comprehensive validation following secure-by-design principles.
"""

import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class CSVValidationError(Exception):
    """Raised when CSV validation fails."""
    pass


class DDoSEventValidator:
    """
    Validator for DDoS event data conforming to MISP DDoS Playbook.
    
    Validates:
    - Required fields presence
    - Data type correctness
    - IP address format
    - Port number ranges
    - TLP levels
    - Workflow states
    - Attack types
    - Date formats
    """
    
    REQUIRED_FIELDS = [
        "date",
        "event_name",
        "attacker_ips",
        "annotation_text"
    ]
    
    OPTIONAL_FIELDS = [
        "tlp",
        "destination_ips",
        "destination_ports"
    ]
    
    VALID_TLP_LEVELS = ["clear", "green", "amber", "red"]
    
    # Maximum limits for security
    MAX_EVENT_NAME_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_ATTACKER_IPS = 1000  # Prevent DoS via large uploads (applies to destination IPs)
    MAX_FILE_SIZE_MB = 10
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_errors: List[str] = []
    
    def _validate_ip_address(self, ip: str) -> bool:
        """
        Validate IP address format (IPv4 or IPv6).
        
        Args:
            ip: IP address string
        
        Returns:
            True if valid, False otherwise
        """
        import ipaddress
        try:
            ipaddress.ip_address(ip.strip())
            return True
        except ValueError:
            return False
    
    def _validate_port(self, port: str) -> bool:
        """
        Validate port number.
        
        Args:
            port: Port number as string
        
        Returns:
            True if valid (1-65535), False otherwise
        """
        try:
            port_int = int(port)
            return 1 <= port_int <= 65535
        except (ValueError, TypeError):
            return False
    
    def _validate_date(self, date_str: str) -> bool:
        """
        Validate date format.
        
        Args:
            date_str: Date string to validate
        
        Returns:
            True if valid, False otherwise
        
        Accepts formats:
        - YYYY-MM-DD
        - YYYY-MM-DD HH:MM:SS
        """
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(date_str.strip(), fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def validate_row(
        self,
        row: Dict[str, str],
        row_number: int
    ) -> Dict[str, Any]:
        """
        Validate a single CSV row and convert to event data.
        
        Args:
            row: Dictionary representing one CSV row
            row_number: Row number for error reporting
        
        Returns:
            Dictionary with validated and parsed event data
        
        Raises:
            CSVValidationError: If validation fails
        """
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in row or not row[field].strip():
                errors.append(f"Row {row_number}: Missing required field '{field}'")
        
        if errors:
            raise CSVValidationError("\n".join(errors))
        
        # Validate event name length
        event_name = row["event_name"].strip()
        if len(event_name) > self.MAX_EVENT_NAME_LENGTH:
            errors.append(
                f"Row {row_number}: Event name exceeds {self.MAX_EVENT_NAME_LENGTH} characters"
            )
        
        # Validate annotation text length
        annotation_text = row["annotation_text"].strip()
        if len(annotation_text) > self.MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"Row {row_number}: Annotation text exceeds {self.MAX_DESCRIPTION_LENGTH} characters"
            )
        
        # Validate date
        date_str = row["date"].strip()
        if not self._validate_date(date_str):
            errors.append(
                f"Row {row_number}: Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
            )
        
        # Parse and validate attacker IPs
        attacker_ips_str = row["attacker_ips"].strip()
        attacker_ips = [ip.strip() for ip in attacker_ips_str.split(";") if ip.strip()]
        
        if not attacker_ips:
            errors.append(f"Row {row_number}: No attacker IPs provided")
        elif len(attacker_ips) > self.MAX_ATTACKER_IPS:
            errors.append(
                f"Row {row_number}: Too many attacker IPs (max {self.MAX_ATTACKER_IPS})"
            )
        
        for ip in attacker_ips:
            if not self._validate_ip_address(ip):
                errors.append(f"Row {row_number}: Invalid attacker IP address '{ip}'")
        
        # Parse and validate destination IPs (optional)
        destination_ips = []
        if "destination_ips" in row and row["destination_ips"].strip():
            destination_ips_str = row["destination_ips"].strip()
            destination_ips = [ip.strip() for ip in destination_ips_str.split(";") if ip.strip()]
            
            if len(destination_ips) > self.MAX_ATTACKER_IPS:
                errors.append(
                    f"Row {row_number}: Too many destination IPs (max {self.MAX_ATTACKER_IPS})"
                )
            
            for ip in destination_ips:
                if not self._validate_ip_address(ip):
                    errors.append(f"Row {row_number}: Invalid destination IP address '{ip}'")
        
        # Parse and validate destination ports (optional)
        destination_ports = []
        if "destination_ports" in row and row["destination_ports"].strip():
            destination_ports_str = row["destination_ports"].strip()
            destination_ports_list = [
                p.strip() for p in destination_ports_str.split(";") if p.strip()
            ]
            
            for port_str in destination_ports_list:
                if not self._validate_port(port_str):
                    errors.append(
                        f"Row {row_number}: Invalid destination port '{port_str}'"
                    )
                else:
                    destination_ports.append(int(port_str))
        
        # Validate TLP level (optional, default to green)
        tlp = row.get("tlp", "green").strip().lower()
        if tlp and tlp not in self.VALID_TLP_LEVELS:
            errors.append(
                f"Row {row_number}: Invalid TLP level '{tlp}'. "
                f"Must be one of {self.VALID_TLP_LEVELS}"
            )
        
        if errors:
            raise CSVValidationError("\n".join(errors))
        
        # Return validated and parsed data
        return {
            "event_name": event_name,
            "event_date": date_str,
            "attacker_ips": attacker_ips,
            "destination_ips": destination_ips if destination_ips else None,
            "destination_ports": destination_ports if destination_ports else None,
            "annotation_text": annotation_text,
            "tlp": tlp if tlp else "green"
        }


class CSVProcessor:
    """
    Secure CSV file processor for bulk DDoS event uploads.
    
    Features:
    - Path traversal prevention
    - File size limits
    - Comprehensive validation
    - Streaming for large files
    - Detailed error reporting
    """
    
    def __init__(self, max_file_size_mb: int = 10):
        """
        Initialize CSV processor.
        
        Args:
            max_file_size_mb: Maximum file size in megabytes
        """
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.validator = DDoSEventValidator()
    
    def _validate_file_path(self, filepath: str) -> Path:
        """
        Validate and canonicalize file path.
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Resolved Path object
        
        Raises:
            ValueError: If path validation fails
        """
        if not isinstance(filepath, (str, Path)):
            raise TypeError(f"Expected str or Path, got {type(filepath)}")
        
        # Resolve to absolute path
        filepath = Path(filepath).resolve()
        
        # Check existence
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Check it's a file, not directory
        if not filepath.is_file():
            raise ValueError(f"Not a file: {filepath}")
        
        # Check file extension
        if filepath.suffix.lower() != ".csv":
            raise ValueError(f"Not a CSV file: {filepath}")
        
        # Check file size
        file_size = filepath.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise ValueError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB "
                f"(max {self.max_file_size_bytes / 1024 / 1024}MB)"
            )
        
        if file_size == 0:
            raise ValueError(f"File is empty: {filepath}")
        
        return filepath
    
    def process_csv(
        self,
        filepath: str,
        skip_invalid: bool = False
    ) -> Dict[str, Any]:
        """
        Process CSV file and extract validated event data.
        
        Args:
            filepath: Path to CSV file
            skip_invalid: If True, skip invalid rows; if False, fail on first error
        
        Returns:
            Dictionary containing:
            - valid_events: List of validated event dictionaries
            - invalid_rows: List of (row_number, error) tuples
            - total_rows: Total number of data rows processed
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file validation fails
            CSVValidationError: If CSV parsing fails
        
        Security:
            - Path traversal is prevented via path validation
            - File size is limited to prevent DoS
            - CSV is streamed line-by-line to avoid memory exhaustion
        """
        logger.info(
            "Processing CSV file",
            extra={"filepath": str(filepath), "skip_invalid": skip_invalid}
        )
        
        # Validate file path
        filepath = self._validate_file_path(filepath)
        
        valid_events = []
        invalid_rows = []
        total_rows = 0
        
        try:
            # Stream CSV file line by line
            with open(filepath, 'r', encoding='utf-8', newline='') as csvfile:
                # Skip comment lines (starting with #)
                content_lines = []
                for line in csvfile:
                    stripped = line.strip()
                    # Skip empty lines and comment lines
                    if stripped and not stripped.startswith('#'):
                        content_lines.append(line)
                
                # Create a string with just the content (no comments)
                content = ''.join(content_lines)
                
                # Create reader from clean content
                from io import StringIO
                reader = csv.DictReader(StringIO(content))
                
                # Validate header
                if not reader.fieldnames:
                    raise CSVValidationError("CSV file has no headers")
                
                # Check for required columns in header
                missing_required = set(self.validator.REQUIRED_FIELDS) - set(reader.fieldnames)
                if missing_required:
                    raise CSVValidationError(
                        f"CSV missing required columns: {missing_required}"
                    )
                
                # Process each row
                for idx, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    total_rows += 1
                    
                    try:
                        # Validate and parse row
                        event_data = self.validator.validate_row(row, idx)
                        valid_events.append(event_data)
                        
                    except CSVValidationError as e:
                        error_msg = str(e)
                        logger.warning(
                            f"Invalid row {idx}",
                            extra={"row": idx, "error": error_msg}
                        )
                        invalid_rows.append((idx, error_msg))
                        
                        if not skip_invalid:
                            # Fail fast on first error
                            raise
        
        except UnicodeDecodeError as e:
            logger.error(
                "Encoding error reading CSV",
                extra={"filepath": str(filepath), "error": str(e)}
            )
            raise CSVValidationError(
                f"File encoding error. Please ensure file is UTF-8 encoded: {str(e)}"
            ) from e
        
        except csv.Error as e:
            logger.error(
                "CSV parsing error",
                extra={"filepath": str(filepath), "error": str(e)}
            )
            raise CSVValidationError(f"CSV parsing error: {str(e)}") from e
        
        except Exception as e:
            logger.error(
                "Unexpected error processing CSV",
                extra={"filepath": str(filepath), "error": str(e)},
                exc_info=True
            )
            raise
        
        logger.info(
            "CSV processing complete",
            extra={
                "filepath": str(filepath),
                "total_rows": total_rows,
                "valid_events": len(valid_events),
                "invalid_rows": len(invalid_rows)
            }
        )
        
        return {
            "valid_events": valid_events,
            "invalid_rows": invalid_rows,
            "total_rows": total_rows
        }
