#!/usr/bin/env python3
"""
Performance Benchmarks for EchoScan
Tests performance and scalability with pytest-benchmark
"""

import pytest
import asyncio
import time
import concurrent.futures
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import echoverifier
import detector_registry


class TestPerformanceBenchmarks:
    """Performance benchmarks for EchoScan components."""
    
    @pytest.fixture
    def sample_inputs(self):
        """Generate sample inputs for benchmarking."""
        return [
            "Short test",
            "Medium length test input with some complexity and patterns to analyze",
            "Very long text input " * 50 + " with repetitive patterns and complex structure",
            "Unicode test: 你好世界 🌍 مرحبا بالعالم Здравствуй мир",
            "Code snippet: def test(): return 'hello world'.upper()",
            "Mixed content with numbers 12345 and symbols !@#$%^&*()",
        ]
    
    def test_echoverifier_basic_performance(self, benchmark, sample_inputs):
        """Benchmark basic EchoVerifier performance."""
        def run_verification():
            return echoverifier.run(sample_inputs[1], mode="verify")
        
        result = benchmark(run_verification)
        
        # Validate result structure
        assert "verdict" in result
        assert "delta_s" in result
        assert "explanation" in result
    
    def test_echoverifier_batch_performance(self, benchmark, sample_inputs):
        """Benchmark batch processing performance."""
        def run_batch_verification():
            results = []
            for inp in sample_inputs:
                result = echoverifier.run(inp, mode="verify")
                results.append(result)
            return results
        
        results = benchmark(run_batch_verification)
        
        assert len(results) == len(sample_inputs)
        for result in results:
            assert "verdict" in result
    
    def test_detector_registry_performance(self, benchmark):
        """Benchmark detector registry loading performance."""
        def load_registry():
            registry = detector_registry.DetectorRegistry()
            return registry.get_registry_info()
        
        info = benchmark(load_registry)
        
        assert "detector_counts" in info
        assert info["detector_counts"]["total"] > 0
    
    @pytest.mark.parametrize("input_size", [10, 100, 1000, 5000])
    def test_input_size_scaling(self, benchmark, input_size):
        """Test how performance scales with input size."""
        large_input = "Test pattern " * input_size
        
        def run_large_input():
            return echoverifier.run(large_input, mode="verify")
        
        result = benchmark(run_large_input)
        
        assert result["verdict"] in ["Authentic", "Plausible", "Hallucination"]
        # Large inputs should typically be flagged as synthetic due to repetition
        if input_size > 500:
            assert result["verdict"] in ["Plausible", "Hallucination"]


class TestAsyncPerformance:
    """Test asynchronous performance capabilities."""
    
    @pytest.mark.asyncio
    async def test_concurrent_verification(self):
        """Test concurrent verification performance."""
        inputs = [
            "Concurrent test 1",
            "Concurrent test 2", 
            "Concurrent test 3",
            "Concurrent test 4",
            "Concurrent test 5"
        ]
        
        async def verify_async(text):
            """Async wrapper for verification."""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, echoverifier.run, text, "verify")
        
        start_time = time.time()
        
        # Run concurrent verifications
        tasks = [verify_async(inp) for inp in inputs]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Run sequential verifications for comparison
        start_time = time.time()
        sequential_results = []
        for inp in inputs:
            result = echoverifier.run(inp, mode="verify")
            sequential_results.append(result)
        end_time = time.time()
        sequential_time = end_time - start_time
        
        print(f"Concurrent time: {concurrent_time:.4f}s")
        print(f"Sequential time: {sequential_time:.4f}s")
        print(f"Speedup: {sequential_time/concurrent_time:.2f}x")
        
        assert len(results) == len(inputs)
        for result in results:
            assert "verdict" in result
    
    def test_threadpool_batch_processing(self):
        """Test threadpool-based batch processing."""
        inputs = ["Batch test " + str(i) for i in range(20)]
        
        def process_batch_sync():
            """Synchronous batch processing."""
            return [echoverifier.run(inp, mode="verify") for inp in inputs]
        
        def process_batch_threadpool():
            """Threadpool batch processing."""
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(echoverifier.run, inp, "verify") for inp in inputs]
                return [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Time both approaches
        start_sync = time.time()
        sync_results = process_batch_sync()
        sync_time = time.time() - start_sync
        
        start_thread = time.time()
        thread_results = process_batch_threadpool()
        thread_time = time.time() - start_thread
        
        print(f"Synchronous time: {sync_time:.4f}s")
        print(f"Threadpool time: {thread_time:.4f}s")
        print(f"Speedup: {sync_time/thread_time:.2f}x")
        
        assert len(sync_results) == len(inputs)
        assert len(thread_results) == len(inputs)


class TestScalabilityBenchmarks:
    """Test system scalability under load."""
    
    @pytest.mark.parametrize("batch_size", [1, 10, 50, 100])
    def test_batch_size_scalability(self, benchmark, batch_size):
        """Test scalability with different batch sizes."""
        inputs = [f"Scalability test {i}" for i in range(batch_size)]
        
        def process_batch():
            results = []
            for inp in inputs:
                result = echoverifier.run(inp, mode="verify")
                results.append(result)
            return results
        
        results = benchmark(process_batch)
        
        assert len(results) == batch_size
        
        # Calculate throughput
        throughput = batch_size / benchmark.stats.mean
        print(f"Batch size: {batch_size}, Throughput: {throughput:.2f} ops/sec")
    
    def test_memory_usage_scaling(self):
        """Test memory usage with increasing load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process increasing amounts of data
        for size in [10, 50, 100, 200]:
            inputs = [f"Memory test {i} " * 10 for i in range(size)]
            
            for inp in inputs:
                echoverifier.run(inp, mode="verify")
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            print(f"Processed {size} items, Memory: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
            
            # Memory usage shouldn't grow excessively
            assert memory_increase < size * 0.1  # Less than 0.1MB per item


def run_performance_suite():
    """Run the complete performance benchmark suite."""
    print("🏃‍♂️ Running EchoScan Performance Benchmark Suite")
    print("=" * 60)
    
    # Run pytest with benchmark plugin
    pytest.main([
        __file__,
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--benchmark-columns=mean,stddev,min,max",
        "-v"
    ])


if __name__ == "__main__":
    run_performance_suite()