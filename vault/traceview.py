"""TraceView module for result tracking."""

class TraceView:
    def __init__(self):
        self.traces = []
        
    def write(self, results):
        """Write trace data."""
        self.traces.append(results)
        
    def summary(self, results):
        """Generate summary of trace data."""
        sbsh_count = len([t for t in self.traces if "sbsh" in t])
        return f"trace_summary: {len(self.traces)} entries, {sbsh_count} SBSH traces"

# Global traceview instance  
traceview = TraceView()