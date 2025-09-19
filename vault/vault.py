"""Vault storage module with retry logic and local backup."""

import json
import time
import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class Vault:
    """Enhanced vault with retry logic and local backup functionality."""
    
    def __init__(self, 
                 backup_dir: str = "vault_backup",
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 backup_enabled: bool = True):
        """Initialize vault with enhanced logging capabilities.
        
        Args:
            backup_dir: Directory for local backup files
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
            backup_enabled: Whether to enable local backup
        """
        self.entries = []
        self.backup_dir = Path(backup_dir)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backup_enabled = backup_enabled
        self.lock = threading.Lock()
        
        # Create backup directory
        if self.backup_enabled:
            self.backup_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.log_attempts = 0
        self.successful_logs = 0
        self.failed_logs = 0
        self.backup_writes = 0
        
    def log(self, results: Dict[str, Any]) -> bool:
        """Log results to vault with retry and fallback logic.
        
        Args:
            results: Results to log to vault
            
        Returns:
            True if logging was successful, False otherwise
        """
        self.log_attempts += 1
        
        # Try to log to main vault
        for attempt in range(self.max_retries + 1):
            try:
                success = self._try_vault_log(results, attempt)
                if success:
                    with self.lock:
                        self.entries.append(results)
                        self.successful_logs += 1
                    return True
                    
            except Exception as e:
                print(f"[VAULT] Log attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    # Final attempt failed, use backup
                    print(f"[VAULT] All retry attempts failed, using local backup")
                    return self._backup_log(results, str(e))
        
        return False
    
    def _try_vault_log(self, results: Dict[str, Any], attempt: int) -> bool:
        """Attempt to log to vault (simulated - can be extended for real vault).
        
        Args:
            results: Results to log
            attempt: Current attempt number
            
        Returns:
            True if successful, False otherwise
        """
        # Simulate potential vault failures
        # In a real implementation, this would make actual vault API calls
        
        # Simulate random failures for testing (remove in production)
        import random
        if random.random() < 0.1:  # 10% failure rate for testing
            raise Exception("Simulated vault connection failure")
        
        # Add logging metadata
        results["vault_metadata"] = {
            "logged_at": datetime.now().isoformat(),
            "attempt": attempt + 1,
            "vault_id": f"vault_entry_{len(self.entries) + 1}"
        }
        
        return True
    
    def _backup_log(self, results: Dict[str, Any], error_msg: str) -> bool:
        """Write to local backup when vault logging fails.
        
        Args:
            results: Results to backup
            error_msg: Error message from vault failure
            
        Returns:
            True if backup was successful, False otherwise
        """
        if not self.backup_enabled:
            self.failed_logs += 1
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_filename = f"vault_backup_{timestamp}.json"
            backup_filepath = self.backup_dir / backup_filename
            
            backup_entry = {
                "timestamp": datetime.now().isoformat(),
                "vault_error": error_msg,
                "backup_reason": "Vault logging failed after retries",
                "data": results
            }
            
            with open(backup_filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_entry, f, indent=2)
            
            # Still add to in-memory entries for consistency
            with self.lock:
                results["backup_metadata"] = {
                    "backup_file": str(backup_filepath),
                    "backup_reason": "Vault logging failed",
                    "error": error_msg
                }
                self.entries.append(results)
                self.backup_writes += 1
            
            print(f"[VAULT BACKUP] Data saved to local backup: {backup_filepath}")
            return True
            
        except Exception as e:
            print(f"[VAULT BACKUP ERROR] Failed to write backup: {e}")
            self.failed_logs += 1
            return False
    
    def get_backup_files(self) -> list:
        """Get list of backup files.
        
        Returns:
            List of backup file paths
        """
        if not self.backup_enabled or not self.backup_dir.exists():
            return []
        
        return [str(f) for f in self.backup_dir.glob("*.json")]
    
    def restore_from_backup(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """Restore data from a backup file.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Restored data or None if failed
        """
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            return backup_data.get("data")
        except Exception as e:
            print(f"[VAULT] Failed to restore from backup {backup_file}: {e}")
            return None
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """Get vault operation statistics.
        
        Returns:
            Dictionary with vault statistics
        """
        with self.lock:
            return {
                "total_entries": len(self.entries),
                "log_attempts": self.log_attempts,
                "successful_logs": self.successful_logs,
                "failed_logs": self.failed_logs,
                "backup_writes": self.backup_writes,
                "backup_files": len(self.get_backup_files()),
                "success_rate": (self.successful_logs / self.log_attempts * 100) if self.log_attempts > 0 else 0,
                "backup_enabled": self.backup_enabled
            }
        
    def last_entry_ref(self):
        """Get reference to last entry."""
        return f"vault_entry_{len(self.entries)}"
    
    def safe_log(self, results: Dict[str, Any], critical: bool = False) -> Dict[str, Any]:
        """Safe logging method that always returns status information.
        
        Args:
            results: Results to log
            critical: Whether this is critical data that must be preserved
            
        Returns:
            Dictionary with logging status information
        """
        start_time = time.time()
        success = self.log(results)
        end_time = time.time()
        
        status = {
            "vault_logged": success,
            "log_duration": end_time - start_time,
            "critical": critical,
            "timestamp": datetime.now().isoformat()
        }
        
        if not success and critical:
            # For critical data, try additional backup methods
            status["emergency_backup"] = self._emergency_backup(results)
        
        return status
    
    def _emergency_backup(self, results: Dict[str, Any]) -> bool:
        """Emergency backup for critical data when all else fails.
        
        Args:
            results: Critical results to backup
            
        Returns:
            True if emergency backup succeeded
        """
        try:
            # Create emergency backup in a different location
            emergency_dir = Path("emergency_backup")
            emergency_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            emergency_file = emergency_dir / f"emergency_{timestamp}.json"
            
            emergency_data = {
                "timestamp": datetime.now().isoformat(),
                "critical_data": True,
                "backup_reason": "Emergency backup - all vault logging failed",
                "data": results
            }
            
            with open(emergency_file, 'w', encoding='utf-8') as f:
                json.dump(emergency_data, f, indent=2)
            
            print(f"[EMERGENCY BACKUP] Critical data saved: {emergency_file}")
            return True
            
        except Exception as e:
            print(f"[EMERGENCY BACKUP FAILED] {e}")
            return False

# Global vault instance
vault = Vault()