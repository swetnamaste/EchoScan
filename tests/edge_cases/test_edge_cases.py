#!/usr/bin/env python3
"""
Edge Case Test Harness for EchoScan
Tests ultra-minimal inputs, unicode anomalies, adversarial attacks, and non-English text.
Includes replayable vectors with ΔS validation.
"""

import pytest
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import echoverifier


class EdgeCaseTestHarness:
    """Test harness for edge cases with ΔS validation and replayable vectors."""
    
    def __init__(self):
        self.test_vectors = []
        self.delta_s_thresholds = {
            "minimal": 0.1,      # Ultra-minimal inputs may have higher variance
            "unicode": 0.15,     # Unicode can introduce encoding variations
            "adversarial": 0.2,  # Adversarial inputs expected to be unstable
            "non_english": 0.12  # Non-English text moderate variation
        }
    
    def record_test_vector(self, input_data: str, expected_category: str, result: dict):
        """Record test vector for replaying and validation."""
        vector = {
            "input": input_data,
            "category": expected_category,
            "delta_s": result["delta_s"],
            "verdict": result["verdict"],
            "explanation": result.get("explanation", ""),
            "glyph_id": result["glyph_id"],
            "echo_sense": result["echo_sense"],
            "timestamp": "test_vector"
        }
        self.test_vectors.append(vector)
        return vector
    
    def validate_delta_s(self, category: str, delta_s: float) -> bool:
        """Validate ΔS is within expected thresholds for category."""
        return delta_s <= self.delta_s_thresholds.get(category, 0.1)
    
    def replay_vectors(self) -> bool:
        """Replay all recorded vectors and validate consistency."""
        all_passed = True
        for vector in self.test_vectors:
            result = echoverifier.run(vector["input"], mode="verify")
            
            # Allow for some variance in ΔS but check it's stable
            delta_s_diff = abs(result["delta_s"] - vector["delta_s"])
            if delta_s_diff > 0.001:  # Small tolerance for floating point precision
                print(f"❌ ΔS instability for '{vector['input'][:20]}...': {delta_s_diff:.6f}")
                all_passed = False
            
            # Verdict should be consistent
            if result["verdict"] != vector["verdict"]:
                print(f"❌ Verdict changed for '{vector['input'][:20]}...': {vector['verdict']} -> {result['verdict']}")
                all_passed = False
                
        return all_passed


@pytest.fixture
def edge_harness():
    """Fixture providing edge case test harness."""
    return EdgeCaseTestHarness()


class TestUltraMinimal:
    """Test ultra-minimal inputs (1 char, empty, etc.)."""
    
    def test_single_character(self, edge_harness):
        """Test single character inputs."""
        test_cases = ["a", "1", "!", "🔥", "中"]
        
        for char in test_cases:
            result = echoverifier.run(char, mode="verify")
            vector = edge_harness.record_test_vector(char, "minimal", result)
            
            # Validate basic structure
            assert "verdict" in result
            assert "delta_s" in result
            assert "explanation" in result
            assert result["glyph_id"].startswith("GHX-")
            
            # ΔS should be within minimal threshold
            assert edge_harness.validate_delta_s("minimal", result["delta_s"]), \
                f"ΔS too high for '{char}': {result['delta_s']}"
            
            print(f"✅ Single char '{char}': {result['verdict']} (ΔS: {result['delta_s']:.6f})")
    
    def test_empty_and_whitespace(self, edge_harness):
        """Test empty and whitespace-only inputs."""
        test_cases = ["", " ", "\n", "\t", "   ", "\n\n\n"]
        
        for inp in test_cases:
            result = echoverifier.run(inp, mode="verify")
            vector = edge_harness.record_test_vector(inp, "minimal", result)
            
            # Should handle gracefully without crashing
            assert result is not None
            assert "verdict" in result
            print(f"✅ Whitespace test '{repr(inp)}': {result['verdict']}")


class TestUnicodeAnomalies:
    """Test unicode edge cases and encoding anomalies."""
    
    def test_unicode_combinations(self, edge_harness):
        """Test complex unicode combinations."""
        test_cases = [
            "👨‍💻",  # Zero-width joiner emoji
            "é",      # Composed character
            "e\u0301",  # Decomposed character (e + combining acute)
            "🏳️‍🌈",    # Rainbow flag (multiple codepoints)
            "А",      # Cyrillic A (looks like Latin A)
            "𝓗𝓮𝓵𝓵𝓸",  # Mathematical script
            "\u200B\u200C\u200D",  # Zero-width characters
            "Hello\uFEFFWorld",  # Byte order mark
        ]
        
        for text in test_cases:
            result = echoverifier.run(text, mode="verify")
            vector = edge_harness.record_test_vector(text, "unicode", result)
            
            assert result["verdict"] in ["Authentic", "Plausible", "Hallucination"]
            assert edge_harness.validate_delta_s("unicode", result["delta_s"]), \
                f"ΔS too high for unicode '{text}': {result['delta_s']}"
            
            print(f"✅ Unicode '{repr(text)}': {result['verdict']} (ΔS: {result['delta_s']:.6f})")
    
    def test_mixed_scripts(self, edge_harness):
        """Test mixed writing systems."""
        test_cases = [
            "Hello 世界",  # Latin + Chinese
            "مرحبا Hello שלום",  # Arabic + Latin + Hebrew
            "Привет こんにちは नमस्ते",  # Cyrillic + Japanese + Devanagari
            "Test テスト تست टेस्ट",  # Multi-script test word
        ]
        
        for text in test_cases:
            result = echoverifier.run(text, mode="verify")
            vector = edge_harness.record_test_vector(text, "unicode", result)
            
            assert result["explanation"] is not None
            print(f"✅ Mixed script '{text}': {result['verdict']}")


class TestAdversarialSymbolic:
    """Test adversarial symbolic attacks."""
    
    def test_hash_collision_attempts(self, edge_harness):
        """Test inputs designed to cause hash collisions."""
        # Pairs that might cause similar hashes
        collision_pairs = [
            ("abcdef", "fedcba"),
            ("123456", "654321"),
            ("hello world", "dlrow olleh"),
            ("AAAAAAAAAA", "BBBBBBBBBB"),
            ("0000000000", "1111111111"),
        ]
        
        for pair in collision_pairs:
            results = []
            for text in pair:
                result = echoverifier.run(text, mode="verify")
                vector = edge_harness.record_test_vector(text, "adversarial", result)
                results.append(result)
            
            # Should produce different glyph IDs and ΔS values
            assert results[0]["glyph_id"] != results[1]["glyph_id"], \
                f"Glyph ID collision: {pair}"
            
            print(f"✅ Collision test '{pair[0]}' vs '{pair[1]}': Different signatures")
    
    def test_pattern_injection(self, edge_harness):
        """Test pattern-based injection attacks."""
        attack_patterns = [
            "ABABABABABABAB" * 10,  # Repetitive pattern
            "".join([chr(i) for i in range(32, 127)]) * 3,  # All ASCII
            "🔥" * 100,  # Emoji flood
            "A" * 1000,  # Single character flood
            "01" * 500,  # Binary pattern
            "Lorem ipsum " * 50,  # Repeated real text
        ]
        
        for pattern in attack_patterns:
            result = echoverifier.run(pattern, mode="verify")
            vector = edge_harness.record_test_vector(pattern[:50] + "...", "adversarial", result)
            
            # Should detect as likely synthetic/hallucination
            assert result["verdict"] in ["Plausible", "Hallucination"], \
                f"Pattern '{pattern[:20]}...' should be flagged"
            
            print(f"✅ Pattern attack detected: {result['verdict']}")


class TestNonEnglishText:
    """Test non-English language texts."""
    
    def test_natural_languages(self, edge_harness):
        """Test various natural languages."""
        language_texts = [
            ("Chinese", "这是一个测试文本，用于验证系统的语言处理能力。"),
            ("Japanese", "これはシステムの日本語処理能力をテストするためのサンプルテキストです。"),
            ("Arabic", "هذا نص تجريبي لاختبار قدرة النظام على معالجة النصوص العربية."),
            ("Russian", "Это тестовый текст для проверки возможностей системы по обработке русского языка."),
            ("Hindi", "यह सिस्टम की हिंदी भाषा प्रसंस्करण क्षमताओं का परीक्षण करने के लिए एक परीक्षण पाठ है।"),
            ("Korean", "이것은 시스템의 한국어 처리 능력을 테스트하기 위한 샘플 텍스트입니다."),
            ("German", "Dies ist ein Testtext zur Überprüfung der deutschen Sprachverarbeitungsfähigkeiten des Systems."),
            ("French", "Ceci est un texte de test pour vérifier les capacités de traitement de la langue française du système."),
        ]
        
        for lang_name, text in language_texts:
            result = echoverifier.run(text, mode="verify")
            vector = edge_harness.record_test_vector(text, "non_english", result)
            
            assert result["verdict"] in ["Authentic", "Plausible", "Hallucination"]
            assert edge_harness.validate_delta_s("non_english", result["delta_s"]), \
                f"ΔS too high for {lang_name}: {result['delta_s']}"
            
            print(f"✅ {lang_name}: {result['verdict']} (ΔS: {result['delta_s']:.6f})")
    
    def test_code_mixed_content(self, edge_harness):
        """Test code mixed with natural language."""
        code_texts = [
            "def hello(): return 'Hello World'  # This is a Python function",
            "SELECT * FROM users WHERE id = 1; -- SQL query example",
            "<html><body>Hello World</body></html>  HTML content here",
            "{\n  \"name\": \"test\",\n  \"value\": 42\n}  JSON data structure",
            "console.log('Hello'); // JavaScript code snippet",
        ]
        
        for code in code_texts:
            result = echoverifier.run(code, mode="verify")
            vector = edge_harness.record_test_vector(code, "non_english", result)
            
            # Code often looks synthetic but may be plausible
            assert result["verdict"] in ["Plausible", "Hallucination"]
            print(f"✅ Code content: {result['verdict']}")


class TestVectorReplay:
    """Test vector replay and consistency validation."""
    
    def test_replay_consistency(self, edge_harness):
        """Run a comprehensive test and validate replay consistency."""
        # Run a variety of tests to populate vectors
        test_inputs = [
            "a", "Hello", "🔥", "测试", "AAAAAAAA", "def test(): pass"
        ]
        
        for inp in test_inputs:
            result = echoverifier.run(inp, mode="verify")
            edge_harness.record_test_vector(inp, "replay_test", result)
        
        # Replay all vectors and validate consistency
        replay_success = edge_harness.replay_vectors()
        assert replay_success, "Vector replay failed - inconsistent results detected"
        
        print(f"✅ All {len(edge_harness.test_vectors)} vectors replayed consistently")
    
    def test_export_vectors(self, edge_harness):
        """Export test vectors for external validation."""
        # Generate some test vectors
        inputs = ["test", "🌟", "код", "PATTERN" * 5]
        for inp in inputs:
            result = echoverifier.run(inp, mode="verify")
            edge_harness.record_test_vector(inp, "export_test", result)
        
        # Export vectors
        vectors_json = json.dumps(edge_harness.test_vectors, indent=2, ensure_ascii=False)
        
        # Save to file for potential external use
        vectors_file = Path(__file__).parent / "test_vectors_export.json"
        with open(vectors_file, "w", encoding="utf-8") as f:
            f.write(vectors_json)
        
        print(f"✅ Exported {len(edge_harness.test_vectors)} test vectors to {vectors_file}")
        assert vectors_file.exists()


def run_edge_case_suite():
    """Run the complete edge case test suite."""
    print("🧪 Running EchoScan Edge Case Test Suite")
    print("=" * 50)
    
    harness = EdgeCaseTestHarness()
    
    # Run all test categories
    test_classes = [TestUltraMinimal, TestUnicodeAnomalies, TestAdversarialSymbolic, TestNonEnglishText]
    
    for test_class in test_classes:
        print(f"\n🔬 Running {test_class.__name__}...")
        instance = test_class()
        
        # Run each test method
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                print(f"  Running {method_name}...")
                try:
                    getattr(instance, method_name)(harness)
                except Exception as e:
                    print(f"  ❌ {method_name} failed: {e}")
                    raise
    
    # Final replay test
    print(f"\n🔄 Final Vector Replay Test...")
    replay_test = TestVectorReplay()
    replay_test.test_replay_consistency(harness)
    replay_test.test_export_vectors(harness)
    
    print(f"\n✅ Edge Case Suite Complete!")
    print(f"Total test vectors recorded: {len(harness.test_vectors)}")
    
    return harness


if __name__ == "__main__":
    # Run as standalone script
    run_edge_case_suite()