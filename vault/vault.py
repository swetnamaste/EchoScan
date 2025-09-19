"""Vault storage module."""

class Vault:
    def __init__(self):
        self.entries = []
        
    def log(self, results):
        """Log results to vault."""
        self.entries.append(results)
        
    def last_entry_ref(self):
        """Get reference to last entry."""
        return f"vault_entry_{len(self.entries)}"

# Global vault instance
vault = Vault()