"""
Auto-Update Module

Checks for updates from GitHub repository and pulls latest changes if available.
Silently proceeds if network is unavailable.
"""

import subprocess
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def check_git_available() -> bool:
    """
    Check if git command is available.
    
    Returns:
        True if git is available, False otherwise
    """
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_git_repository(repo_path: Optional[Path] = None) -> bool:
    """
    Check if the current directory is a git repository.
    
    Args:
        repo_path: Path to check. If None, uses current directory.
    
    Returns:
        True if it's a git repository, False otherwise
    """
    if repo_path is None:
        repo_path = Path.cwd()
    
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=repo_path,
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def check_for_updates(repo_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Check if updates are available from GitHub remote.
    
    Args:
        repo_path: Path to git repository. If None, uses current directory.
    
    Returns:
        Tuple of (updates_available: bool, message: str)
    """
    if repo_path is None:
        repo_path = Path.cwd()
    
    try:
        # Fetch latest from remote (doesn't pull)
        result = subprocess.run(
            ["git", "fetch", "origin"],
            cwd=repo_path,
            capture_output=True,
            timeout=10,
            text=True
        )
        
        # Check if fetch succeeded
        if result.returncode != 0:
            logger.debug(f"Git fetch failed: {result.stderr}")
            return False, "Unable to check for updates (fetch failed)"
        
        # Compare local HEAD with remote HEAD
        local_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            check=True,
            timeout=5,
            text=True
        ).stdout.strip()
        
        remote_head = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=repo_path,
            capture_output=True,
            check=True,
            timeout=5,
            text=True
        ).stdout.strip()
        
        if local_head != remote_head:
            return True, "Updates available"
        else:
            return False, "Already up to date"
            
    except subprocess.TimeoutExpired:
        logger.debug("Git fetch timed out")
        return False, "Network timeout - proceeding anyway"
    except subprocess.SubprocessError as e:
        logger.debug(f"Git check failed: {e}")
        return False, "Unable to check for updates"
    except Exception as e:
        logger.debug(f"Unexpected error checking for updates: {e}")
        return False, "Unable to check for updates"


def pull_updates(repo_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Pull latest updates from GitHub remote.
    
    Args:
        repo_path: Path to git repository. If None, uses current directory.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if repo_path is None:
        repo_path = Path.cwd()
    
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=repo_path,
            capture_output=True,
            timeout=15,
            text=True,
            check=True
        )
        
        if "Already up to date" in result.stdout:
            return True, "Already up to date"
        else:
            return True, "Successfully updated"
            
    except subprocess.TimeoutExpired:
        logger.warning("Git pull timed out")
        return False, "Update timed out - proceeding with current version"
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git pull failed: {e.stderr}")
        return False, f"Update failed: {e.stderr.strip()}"
    except Exception as e:
        logger.warning(f"Unexpected error during pull: {e}")
        return False, "Update failed - proceeding with current version"


def auto_update(silent: bool = False) -> Tuple[bool, str]:
    """
    Automatically check and pull updates from GitHub if available.
    Silently proceeds if network is unavailable or git is not available.
    
    Args:
        silent: If True, suppress console output
    
    Returns:
        Tuple of (updated: bool, message: str)
    """
    # Check if git is available
    if not check_git_available():
        logger.debug("Git not available, skipping auto-update")
        return False, "Git not available"
    
    # Check if we're in a git repository
    if not is_git_repository():
        logger.debug("Not a git repository, skipping auto-update")
        return False, "Not a git repository"
    
    # Check for updates
    updates_available, message = check_for_updates()
    
    if not updates_available:
        logger.debug(f"No updates: {message}")
        return False, message
    
    # Pull updates
    success, pull_message = pull_updates()
    
    if success:
        logger.info(f"Auto-update: {pull_message}")
        return True, pull_message
    else:
        logger.warning(f"Auto-update failed: {pull_message}")
        return False, pull_message
