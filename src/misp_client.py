"""
MISP Client Module

Secure client for interacting with MISP API following defense-in-depth principles.
Implements retry logic, comprehensive error handling, and secure communication.
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Callable
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pymisp import ExpandedPyMISP, MISPEvent, MISPObject, MISPAttribute
from pymisp.exceptions import PyMISPError


logger = logging.getLogger(__name__)


class MISPClientError(Exception):
    """Base exception for MISP client errors."""
    pass


class MISPConnectionError(MISPClientError):
    """Raised when connection to MISP fails."""
    pass


class MISPValidationError(MISPClientError):
    """Raised when data validation fails."""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple = (requests.RequestException, PyMISPError)
):
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"Max retries ({max_attempts}) exceeded for {func.__name__}",
                            extra={"error": str(e), "error_type": type(e).__name__}
                        )
                        raise MISPConnectionError(
                            f"Failed after {max_attempts} attempts: {str(e)}"
                        ) from e
                    
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}. "
                        f"Retrying in {wait_time}s...",
                        extra={
                            "attempt": attempt,
                            "wait_time": wait_time,
                            "error": str(e)
                        }
                    )
                    time.sleep(wait_time)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class MISPClient:
    """
    Secure MISP client with comprehensive error handling and validation.
    
    This client follows security best practices:
    - Validates all inputs at trust boundaries
    - Implements retry logic with exponential backoff
    - Comprehensive error handling and logging
    - Secure defaults for all operations
    
    Security Note:
        - API keys are sensitive credentials - never log or expose them
        - SSL verification can be disabled for self-hosted instances
        - All data is validated before sending to MISP
    """
    
    # MISP DDoS Playbook Constants
    MANDATORY_GLOBAL_TAGS = [
        "tlp:green",  # Default TLP, can be overridden
        "information-security-indicators:incident-type=\"ddos\"",
        "misp-event-type:incident"
    ]
    
    LOCAL_WORKFLOW_TAG_PREFIX = "workflow:state="
    
    # MITRE ATT&CK T1498 - Network Denial of Service (DDoS-specific)
    MITRE_ATTACK_PATTERN = "mitre-attack-pattern:T1498"
    MITRE_GALAXY_CLUSTER = 'misp-galaxy:mitre-attack-pattern="Network Denial of Service - T1498"'
    
    VALID_TLP_LEVELS = ["clear", "green", "amber", "red"]
    
    def __init__(
        self,
        url: str,
        api_key: str,
        verify_ssl: bool = True,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize MISP client with secure configuration.
        
        Args:
            url: MISP instance URL (must be https://)
            api_key: MISP API authentication key
            verify_ssl: Whether to verify SSL certificates (disable for self-hosted)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        
        Raises:
            ValueError: If URL or API key validation fails
            MISPConnectionError: If connection to MISP cannot be established
        """
        # Input validation
        if not isinstance(url, str) or not url:
            raise ValueError("URL must be a non-empty string")
        
        if not isinstance(api_key, str) or not api_key:
            raise ValueError("API key must be a non-empty string")
        
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        
        if timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")
        
        if max_retries < 0:
            raise ValueError(f"Max retries must be non-negative, got {max_retries}")
        
        self.url = url.rstrip("/")
        self._api_key = api_key  # Private to avoid accidental logging
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Suppress SSL warnings if verification is disabled
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning(
                "SSL verification disabled - only use for trusted self-hosted instances"
            )
        
        # Initialize PyMISP client
        try:
            self.client = ExpandedPyMISP(
                url=self.url,
                key=self._api_key,
                ssl=self.verify_ssl,
                timeout=self.timeout
            )
            logger.info(
                "MISP client initialized",
                extra={
                    "url": self.url,
                    "ssl_verify": self.verify_ssl,
                    "timeout": self.timeout
                }
            )
        except Exception as e:
            logger.error(
                "Failed to initialize MISP client",
                extra={"url": self.url, "error": str(e)},
                exc_info=True
            )
            raise MISPConnectionError(f"Failed to initialize MISP client: {str(e)}") from e
        
        # Test connection
        self._test_connection()
    
    @retry_with_backoff(max_attempts=3)
    def _test_connection(self) -> None:
        """
        Test connection to MISP instance.
        
        Raises:
            MISPConnectionError: If connection test fails
        """
        try:
            # Try to get MISP version as a connection test
            version = self.client.misp_instance_version
            logger.info(
                "Successfully connected to MISP",
                extra={"version": version.get("version", "unknown") if isinstance(version, dict) else str(version)}
            )
        except Exception as e:
            logger.error(
                "Connection test failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise MISPConnectionError(f"Failed to connect to MISP: {str(e)}") from e
    
    def _validate_ip_address(self, ip: str) -> bool:
        """
        Validate IP address format.
        
        Args:
            ip: IP address string to validate
        
        Returns:
            True if valid, False otherwise
        """
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _validate_port(self, port: int) -> bool:
        """
        Validate port number.
        
        Args:
            port: Port number to validate
        
        Returns:
            True if valid (1-65535), False otherwise
        """
        return isinstance(port, int) and 1 <= port <= 65535
    
    def _sanitize_tag(self, tag: str) -> str:
        """
        Sanitize tag input to prevent injection.
        
        Args:
            tag: Tag string to sanitize
        
        Returns:
            Sanitized tag string
        """
        if not isinstance(tag, str):
            raise MISPValidationError(f"Tag must be string, got {type(tag)}")
        
        # Remove potentially dangerous characters
        sanitized = tag.strip()
        
        # Validate tag format (alphanumeric, hyphens, colons, equals, quotes)
        import re
        if not re.match(r'^[a-zA-Z0-9:="\-_.]+$', sanitized):
            raise MISPValidationError(
                f"Tag contains invalid characters: {tag}"
            )
        
        return sanitized
    
    @retry_with_backoff(max_attempts=3)
    def create_ddos_event(
        self,
        event_name: str,
        event_date: str,
        attacker_ips: List[str],
        victim_ip: str,
        victim_port: int,
        attacker_ports: Optional[List[int]] = None,
        description: str = "",
        tlp: str = "green",
        workflow_state: str = "new",
        attack_type: str = "direct-flood"
    ) -> Dict[str, Any]:
        """
        Create a DDoS event in MISP following the Streamlined DDoS Playbook.
        
        Args:
            event_name: Name/title of the DDoS event
            event_date: Date of the event (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            attacker_ips: List of attacker IP addresses
            victim_ip: Victim IP address
            victim_port: Victim port number
            attacker_ports: Optional list of attacker ports
            description: Detailed description of the attack
            tlp: Traffic Light Protocol level (clear, green, amber, red)
            workflow_state: Workflow state (always "new" for event creation)
            attack_type: Attack type (direct-flood, amplification, or both)
        
        Returns:
            Dictionary containing the created event details
        
        Raises:
            MISPValidationError: If input validation fails
            MISPConnectionError: If event creation fails
        
        Examples:
            >>> client = MISPClient(url, api_key)
            >>> event = client.create_ddos_event(
            ...     event_name="DDoS Attack on Web Server",
            ...     event_date="2024-01-15",
            ...     attacker_ips=["192.168.1.100", "192.168.1.101"],
            ...     victim_ip="10.0.0.50",
            ...     victim_port=443,
            ...     description="Large-scale DDoS attack"
            ... )
        """
        start_time = time.time()
        logger.info(
            "Creating DDoS event",
            extra={
                "event_name": event_name,
                "event_date": event_date,
                "attacker_count": len(attacker_ips),
                "victim_ip": victim_ip
            }
        )
        
        # Input validation
        if not isinstance(event_name, str) or not event_name.strip():
            raise MISPValidationError("Event name must be a non-empty string")
        
        if not isinstance(event_date, str) or not event_date.strip():
            raise MISPValidationError("Event date must be a non-empty string")
        
        if not isinstance(attacker_ips, list) or not attacker_ips:
            raise MISPValidationError("Attacker IPs must be a non-empty list")
        
        if not isinstance(victim_ip, str) or not self._validate_ip_address(victim_ip):
            raise MISPValidationError(f"Invalid victim IP address: {victim_ip}")
        
        if not self._validate_port(victim_port):
            raise MISPValidationError(f"Invalid victim port: {victim_port}")
        
        # Validate all attacker IPs
        for ip in attacker_ips:
            if not isinstance(ip, str) or not self._validate_ip_address(ip):
                raise MISPValidationError(f"Invalid attacker IP address: {ip}")
        
        # Validate TLP level
        tlp_lower = tlp.lower()
        if tlp_lower not in self.VALID_TLP_LEVELS:
            raise MISPValidationError(
                f"Invalid TLP level: {tlp}. Must be one of {self.VALID_TLP_LEVELS}"
            )
        
        # Workflow state is always "new" for event creation
        # Validation removed - workflow state set to "new" by default
        
        # Validate attack type
        valid_attack_types = ["direct-flood", "amplification", "both"]
        if attack_type not in valid_attack_types:
            raise MISPValidationError(
                f"Invalid attack type: {attack_type}. "
                f"Must be one of {valid_attack_types}"
            )
        
        try:
            # Create MISP event
            event = MISPEvent()
            event.info = event_name
            event.date = event_date
            
            # Add mandatory global tags
            event.add_tag(f"tlp:{tlp_lower}")
            event.add_tag("information-security-indicators:incident-type=\"ddos\"")
            event.add_tag("misp-event-type:incident")
            
            # Add MITRE ATT&CK T1498 tag (Network Denial of Service)
            event.add_tag(self.MITRE_ATTACK_PATTERN)
            
            # Add MITRE ATT&CK T1498 Galaxy Cluster (Network Denial of Service)
            event.add_tag(self.MITRE_GALAXY_CLUSTER)
            logger.debug("Added T1498 Network Denial of Service tag and galaxy cluster")
            
            # Add local workflow tag (always "new" for event creation)
            event.add_tag(f"{self.LOCAL_WORKFLOW_TAG_PREFIX}new")
            
            # Create annotation object for description
            if description:
                annotation = MISPObject("annotation")
                annotation.add_attribute("text", value=description)
                event.add_object(annotation)
            
            # Create ip-port objects for attackers (no confidence tagging)
            for idx, attacker_ip in enumerate(attacker_ips):
                ip_port_obj = MISPObject("ip-port")
                ip_port_obj.add_attribute("ip", value=attacker_ip)
                
                # Add port if available
                if attacker_ports and idx < len(attacker_ports):
                    port = attacker_ports[idx]
                    if self._validate_port(port):
                        ip_port_obj.add_attribute("dst-port", value=str(port))
                
                ip_port_obj.comment = f"Attacker IP {idx + 1}"
                event.add_object(ip_port_obj)
            
            # Create ip-port object for victim
            victim_obj = MISPObject("ip-port")
            victim_obj.add_attribute("ip", value=victim_ip)
            victim_obj.add_attribute("dst-port", value=str(victim_port))
            victim_obj.comment = "Victim IP and Port"
            event.add_object(victim_obj)
            
            # Add event to MISP
            response = self.client.add_event(event, pythonify=True)
            
            duration = time.time() - start_time
            logger.info(
                "DDoS event created successfully",
                extra={
                    "event_id": response.id,
                    "event_name": event_name,
                    "duration_seconds": duration
                }
            )
            
            return {
                "success": True,
                "event_id": response.id,
                "event_uuid": response.uuid,
                "event_name": event_name,
                "url": f"{self.url}/events/view/{response.id}"
            }
            
        except PyMISPError as e:
            logger.error(
                "Failed to create MISP event",
                extra={
                    "event_name": event_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise MISPConnectionError(f"Failed to create event: {str(e)}") from e
        
        except Exception as e:
            logger.error(
                "Unexpected error creating MISP event",
                extra={
                    "event_name": event_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise MISPClientError(f"Unexpected error: {str(e)}") from e
    
    def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an event from MISP by ID.
        
        Args:
            event_id: MISP event ID
        
        Returns:
            Event dictionary or None if not found
        
        Raises:
            MISPConnectionError: If retrieval fails
        """
        if not isinstance(event_id, int) or event_id <= 0:
            raise MISPValidationError(f"Event ID must be positive integer, got {event_id}")
        
        try:
            event = self.client.get_event(event_id, pythonify=True)
            return event.to_dict() if event else None
        except Exception as e:
            logger.error(
                "Failed to retrieve event",
                extra={"event_id": event_id, "error": str(e)},
                exc_info=True
            )
            raise MISPConnectionError(f"Failed to retrieve event {event_id}: {str(e)}") from e
    
    def search_events(
        self,
        tags: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for events in MISP.
        
        Args:
            tags: List of tags to filter by
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        
        Returns:
            List of event dictionaries
        
        Raises:
            MISPConnectionError: If search fails
        """
        try:
            events = self.client.search(
                tags=tags,
                date_from=date_from,
                date_to=date_to,
                pythonify=True
            )
            return [event.to_dict() for event in events] if events else []
        except Exception as e:
            logger.error(
                "Failed to search events",
                extra={"tags": tags, "error": str(e)},
                exc_info=True
            )
            raise MISPConnectionError(f"Failed to search events: {str(e)}") from e
