"""Vault module for storing signatures and results"""

_last_entry = None

def log(results):
    """Log results to vault"""
    global _last_entry
    _last_entry = f"vault_entry_{hash(str(results)) % 10000:04d}"
    return _last_entry

def last_entry_ref():
    """Get reference to last vault entry"""
    return _last_entry or "vault_entry_0000"