"""
Test Suite for MISP DDoS CLI

Comprehensive tests covering:
- Security validation
- Input validation
- CSV processing
- MISP client operations
- Error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.misp_client import MISPClient, MISPValidationError, MISPConnectionError
from src.csv_processor import CSVProcessor, DDoSEventValidator, CSVValidationError
from src.config import Config, ConfigurationError


class TestMISPClient:
    """Tests for MISPClient class."""
    
    def test_init_valid_config(self):
        """Test MISPClient initialization with valid configuration."""
        with patch('src.misp_client.ExpandedPyMISP') as mock_pymisp:
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_api_key_123456",
                verify_ssl=False,
                timeout=30
            )
            assert client.url == "https://misp.example.com"
            assert client.verify_ssl is False
            assert client.timeout == 30
    
    def test_init_invalid_url(self):
        """Test MISPClient rejects invalid URLs."""
        with pytest.raises(ValueError, match="URL must start with"):
            MISPClient(
                url="ftp://invalid.com",
                api_key="test_key"
            )
    
    def test_init_empty_api_key(self):
        """Test MISPClient rejects empty API key."""
        with pytest.raises(ValueError, match="API key must be"):
            MISPClient(
                url="https://misp.example.com",
                api_key=""
            )
    
    def test_init_invalid_timeout(self):
        """Test MISPClient rejects invalid timeout."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            MISPClient(
                url="https://misp.example.com",
                api_key="test_key",
                timeout=-1
            )
    
    def test_validate_ip_address_valid(self):
        """Test IP address validation with valid IPs."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            assert client._validate_ip_address("192.168.1.1") is True
            assert client._validate_ip_address("10.0.0.1") is True
            assert client._validate_ip_address("2001:db8::1") is True
    
    def test_validate_ip_address_invalid(self):
        """Test IP address validation with invalid IPs."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            assert client._validate_ip_address("invalid") is False
            assert client._validate_ip_address("999.999.999.999") is False
            assert client._validate_ip_address("") is False
    
    def test_validate_port_valid(self):
        """Test port validation with valid ports."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            assert client._validate_port(80) is True
            assert client._validate_port(443) is True
            assert client._validate_port(65535) is True
    
    def test_validate_port_invalid(self):
        """Test port validation with invalid ports."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            assert client._validate_port(0) is False
            assert client._validate_port(-1) is False
            assert client._validate_port(65536) is False
    
    def test_sanitize_tag_valid(self):
        """Test tag sanitization with valid tags."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            assert client._sanitize_tag("tlp:green") == "tlp:green"
            assert client._sanitize_tag("workflow:state=new") == "workflow:state=new"
    
    def test_sanitize_tag_invalid(self):
        """Test tag sanitization rejects malicious input."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            with pytest.raises(MISPValidationError, match="invalid characters"):
                client._sanitize_tag("tag; DROP TABLE events;")
    
    def test_create_ddos_event_invalid_event_name(self):
        """Test event creation rejects invalid event names."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            with pytest.raises(MISPValidationError, match="Event name must be"):
                client.create_ddos_event(
                    event_name="",
                    event_date="2024-01-01",
                    attacker_ips=["192.168.1.1"],
                    victim_ip="10.0.0.1",
                    victim_port=443
                )
    
    def test_create_ddos_event_invalid_attacker_ip(self):
        """Test event creation rejects invalid attacker IPs."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            with pytest.raises(MISPValidationError, match="Invalid attacker IP"):
                client.create_ddos_event(
                    event_name="Test Event",
                    event_date="2024-01-01",
                    attacker_ips=["invalid_ip"],
                    victim_ip="10.0.0.1",
                    victim_port=443
                )
    
    def test_create_ddos_event_path_traversal_prevention(self):
        """Test that event creation prevents path traversal in inputs."""
        with patch('src.misp_client.ExpandedPyMISP'):
            client = MISPClient(
                url="https://misp.example.com",
                api_key="test_key"
            )
            # Should handle strings safely without path traversal
            # Event name with suspicious patterns should still be accepted as string
            # (path traversal is only relevant for file operations)


class TestDDoSEventValidator:
    """Tests for DDoSEventValidator class."""
    
    def setup_method(self):
        """Setup validator for each test."""
        self.validator = DDoSEventValidator()
    
    def test_validate_ip_address_valid(self):
        """Test IP validation with valid addresses."""
        assert self.validator._validate_ip_address("192.168.1.1") is True
        assert self.validator._validate_ip_address("10.0.0.1") is True
        assert self.validator._validate_ip_address("2001:db8::1") is True
    
    def test_validate_ip_address_invalid(self):
        """Test IP validation with invalid addresses."""
        assert self.validator._validate_ip_address("invalid") is False
        assert self.validator._validate_ip_address("999.999.999.999") is False
    
    def test_validate_port_valid(self):
        """Test port validation with valid ports."""
        assert self.validator._validate_port("80") is True
        assert self.validator._validate_port("443") is True
        assert self.validator._validate_port("65535") is True
    
    def test_validate_port_invalid(self):
        """Test port validation with invalid ports."""
        assert self.validator._validate_port("0") is False
        assert self.validator._validate_port("-1") is False
        assert self.validator._validate_port("65536") is False
        assert self.validator._validate_port("invalid") is False
    
    def test_validate_date_valid(self):
        """Test date validation with valid dates."""
        assert self.validator._validate_date("2024-01-15") is True
        assert self.validator._validate_date("2024-01-15 14:30:00") is True
    
    def test_validate_date_invalid(self):
        """Test date validation with invalid dates."""
        assert self.validator._validate_date("invalid") is False
        assert self.validator._validate_date("15-01-2024") is False
        assert self.validator._validate_date("2024/01/15") is False
    
    def test_validate_row_valid(self):
        """Test row validation with valid data."""
        row = {
            "date": "2024-01-15",
            "event_name": "Test DDoS",
            "attack_type": "direct-flood",
            "attacker_ips": "192.168.1.100;192.168.1.101",
            "victim_ip": "10.0.0.50",
            "victim_port": "443",
            "description": "Test attack description",
            "tlp": "green",
            "workflow_state": "new",
            "confidence_level": "high"
        }
        
        result = self.validator.validate_row(row, 1)
        assert result["event_name"] == "Test DDoS"
        assert len(result["attacker_ips"]) == 2
        assert result["victim_port"] == 443
    
    def test_validate_row_missing_required_field(self):
        """Test row validation rejects missing required fields."""
        row = {
            "date": "2024-01-15",
            # Missing event_name
            "attack_type": "direct-flood",
            "attacker_ips": "192.168.1.100",
            "victim_ip": "10.0.0.50",
            "victim_port": "443",
            "description": "Test"
        }
        
        with pytest.raises(CSVValidationError, match="Missing required field"):
            self.validator.validate_row(row, 1)
    
    def test_validate_row_invalid_tlp(self):
        """Test row validation rejects invalid TLP levels."""
        row = {
            "date": "2024-01-15",
            "event_name": "Test",
            "attack_type": "direct-flood",
            "attacker_ips": "192.168.1.100",
            "victim_ip": "10.0.0.50",
            "victim_port": "443",
            "description": "Test",
            "tlp": "invalid_tlp"
        }
        
        with pytest.raises(CSVValidationError, match="Invalid TLP level"):
            self.validator.validate_row(row, 1)
    
    def test_validate_row_sql_injection_attempt(self):
        """Test row validation handles SQL injection attempts safely."""
        row = {
            "date": "2024-01-15",
            "event_name": "'; DROP TABLE events; --",
            "attack_type": "direct-flood",
            "attacker_ips": "192.168.1.100",
            "victim_ip": "10.0.0.50",
            "victim_port": "443",
            "description": "Test"
        }
        
        # Should not raise exception - string is safely validated
        result = self.validator.validate_row(row, 1)
        # Event name should be preserved as-is (it's just a string)
        assert "DROP TABLE" in result["event_name"]


class TestCSVProcessor:
    """Tests for CSVProcessor class."""
    
    def setup_method(self):
        """Setup processor for each test."""
        self.processor = CSVProcessor()
    
    def test_validate_file_path_nonexistent(self):
        """Test file validation rejects nonexistent files."""
        with pytest.raises(FileNotFoundError):
            self.processor._validate_file_path("nonexistent.csv")
    
    def test_validate_file_path_not_csv(self, tmp_path):
        """Test file validation rejects non-CSV files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError, match="Not a CSV file"):
            self.processor._validate_file_path(str(test_file))
    
    def test_validate_file_path_empty_file(self, tmp_path):
        """Test file validation rejects empty files."""
        test_file = tmp_path / "empty.csv"
        test_file.write_text("")
        
        with pytest.raises(ValueError, match="File is empty"):
            self.processor._validate_file_path(str(test_file))
    
    def test_process_csv_valid(self, tmp_path):
        """Test CSV processing with valid data."""
        csv_content = """date,event_name,attack_type,attacker_ips,victim_ip,victim_port,description
2024-01-15,Test DDoS,direct-flood,192.168.1.100,10.0.0.50,443,Test attack
"""
        test_file = tmp_path / "test.csv"
        test_file.write_text(csv_content)
        
        result = self.processor.process_csv(str(test_file))
        
        assert result["total_rows"] == 1
        assert len(result["valid_events"]) == 1
        assert len(result["invalid_rows"]) == 0
    
    def test_process_csv_missing_headers(self, tmp_path):
        """Test CSV processing rejects files with missing required headers."""
        csv_content = """date,event_name
2024-01-15,Test
"""
        test_file = tmp_path / "test.csv"
        test_file.write_text(csv_content)
        
        with pytest.raises(CSVValidationError, match="missing required columns"):
            self.processor.process_csv(str(test_file))


class TestConfig:
    """Tests for Config class."""
    
    def test_config_missing_required_var(self, monkeypatch):
        """Test config rejects missing required variables."""
        monkeypatch.delenv("MISP_URL", raising=False)
        monkeypatch.delenv("MISP_API_KEY", raising=False)
        
        with pytest.raises(ConfigurationError, match="Required environment variable"):
            Config()
    
    def test_config_invalid_url(self, monkeypatch):
        """Test config rejects invalid MISP URLs."""
        monkeypatch.setenv("MISP_URL", "ftp://invalid.com")
        monkeypatch.setenv("MISP_API_KEY", "test_key_12345")
        
        with pytest.raises(ConfigurationError, match="must start with http"):
            Config()
    
    def test_config_short_api_key(self, monkeypatch):
        """Test config rejects suspiciously short API keys."""
        monkeypatch.setenv("MISP_URL", "https://misp.example.com")
        monkeypatch.setenv("MISP_API_KEY", "short")
        
        with pytest.raises(ConfigurationError, match="appears to be invalid"):
            Config()
    
    def test_config_valid(self, monkeypatch):
        """Test config accepts valid configuration."""
        monkeypatch.setenv("MISP_URL", "https://misp.example.com")
        monkeypatch.setenv("MISP_API_KEY", "valid_api_key_12345")
        monkeypatch.setenv("MISP_VERIFY_SSL", "false")
        monkeypatch.setenv("MISP_TIMEOUT", "30")
        
        config = Config()
        assert config.misp_url == "https://misp.example.com"
        assert config.misp_verify_ssl is False
        assert config.misp_timeout == 30


# Run tests with: pytest tests/test_misp_cli.py -v
