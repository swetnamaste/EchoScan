"""
Quirk Injection Layer - Detection of human irregularities
Detects fillers, hesitations, tangents, and other human writing patterns as authenticity signals.
"""

import re
from typing import Dict, List, Any, Set
from collections import Counter


class QuirkPatterns:
    """Patterns for detecting human writing quirks."""
    
    # Filler words and expressions
    FILLERS = {
        "um", "uh", "er", "hmm", "well", "like", "you know", "i mean", 
        "sort of", "kind of", "basically", "actually", "literally",
        "obviously", "clearly", "frankly", "honestly", "seriously",
        "anyway", "so", "and", "but", "however", "though", "although"
    }
    
    # Hesitation patterns
    HESITATION_PATTERNS = [
        r'\b(um+|uh+|er+|hmm+)\b',
        r'\.{2,}',  # Multiple dots
        r'--+',     # Dashes
        r'\b\w+\.\.\.\w+\b',  # Word...word patterns
        r'\b(well|so)\s*,',   # Well, So, etc.
    ]
    
    # Tangential expressions
    TANGENT_MARKERS = {
        "by the way", "btw", "speaking of", "that reminds me", "oh", "wait",
        "come to think of it", "now that i think about it", "incidentally",
        "as an aside", "on second thought", "actually", "in fact"
    }
    
    # Colloquial contractions and informal language
    INFORMAL_PATTERNS = [
        r"n't\b",           # Contractions
        r"'m\b", r"'re\b", r"'ve\b", r"'ll\b", r"'d\b",
        r"\bgonna\b", r"\bwanna\b", r"\bkinda\b", r"\bsorta\b",
        r"\byeah\b", r"\byep\b", r"\bnope\b", r"\bokay\b", r"\bok\b"
    ]
    
    # Self-correction patterns
    SELF_CORRECTION_PATTERNS = [
        r'\b\w+\s*--\s*\w+\b',           # word--correction
        r'\b\w+\s*,\s*no\s*,\s*\w+\b',   # word, no, correction
        r'\b\w+\s*\.\s*I mean\s*\w+\b',   # word. I mean correction
        r'\bwait\s*,\s*\w+\b',           # wait, correction
        r'\bsorry\s*,\s*\w+\b',          # sorry, correction
    ]


def detect_fillers(text: str) -> Dict[str, Any]:
    """Detect filler words and calculate density."""
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    total_words = len(words)
    
    if total_words == 0:
        return {"count": 0, "density": 0.0, "types": []}
    
    filler_words = []
    for word in words:
        if word in QuirkPatterns.FILLERS:
            filler_words.append(word)
    
    # Also check for multi-word fillers
    text_phrases = text_lower
    multi_word_fillers = []
    for filler in QuirkPatterns.FILLERS:
        if " " in filler and filler in text_phrases:
            count = len(re.findall(re.escape(filler), text_phrases))
            multi_word_fillers.extend([filler] * count)
    
    all_fillers = filler_words + multi_word_fillers
    filler_types = list(set(all_fillers))
    filler_density = len(all_fillers) / total_words
    
    return {
        "count": len(all_fillers),
        "density": round(filler_density, 6),
        "types": filler_types,
        "frequency": dict(Counter(all_fillers))
    }


def detect_hesitations(text: str) -> Dict[str, Any]:
    """Detect hesitation patterns in text."""
    hesitation_matches = []
    
    for pattern in QuirkPatterns.HESITATION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        hesitation_matches.extend(matches)
    
    # Count ellipses and dashes
    ellipses_count = len(re.findall(r'\.{3,}', text))
    dash_count = len(re.findall(r'--+', text))
    
    return {
        "count": len(hesitation_matches),
        "ellipses": ellipses_count,
        "dashes": dash_count,
        "patterns": hesitation_matches,
        "total_hesitation_markers": len(hesitation_matches) + ellipses_count + dash_count
    }


def detect_tangents(text: str) -> Dict[str, Any]:
    """Detect tangential expressions and topic shifts."""
    text_lower = text.lower()
    tangent_count = 0
    found_markers = []
    
    for marker in QuirkPatterns.TANGENT_MARKERS:
        if marker in text_lower:
            count = len(re.findall(re.escape(marker), text_lower))
            tangent_count += count
            found_markers.extend([marker] * count)
    
    # Look for parenthetical asides
    parenthetical_count = len(re.findall(r'\([^)]+\)', text))
    
    # Look for topic shift patterns
    topic_shift_patterns = [
        r'\banyway\b', r'\bmoving on\b', r'\bback to\b', 
        r'\bas I was saying\b', r'\bwhere was I\b'
    ]
    
    shift_count = 0
    for pattern in topic_shift_patterns:
        shift_count += len(re.findall(pattern, text, re.IGNORECASE))
    
    return {
        "tangent_markers": tangent_count,
        "parenthetical_asides": parenthetical_count,
        "topic_shifts": shift_count,
        "found_markers": found_markers,
        "total_tangents": tangent_count + parenthetical_count + shift_count
    }


def detect_informal_language(text: str) -> Dict[str, Any]:
    """Detect colloquial and informal language patterns."""
    informal_count = 0
    found_patterns = []
    
    for pattern in QuirkPatterns.INFORMAL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        informal_count += len(matches)
        found_patterns.extend(matches)
    
    return {
        "count": informal_count,
        "patterns": found_patterns,
        "density": informal_count / max(len(text.split()), 1)
    }


def detect_self_corrections(text: str) -> Dict[str, Any]:
    """Detect self-correction patterns."""
    correction_count = 0
    found_corrections = []
    
    for pattern in QuirkPatterns.SELF_CORRECTION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        correction_count += len(matches)
        found_corrections.extend(matches)
    
    return {
        "count": correction_count,
        "corrections": found_corrections
    }


def calculate_quirk_score(quirk_data: Dict[str, Dict]) -> float:
    """Calculate overall quirk score based on detected patterns."""
    # Weight different quirk types
    weights = {
        "fillers": 0.3,
        "hesitations": 0.25,
        "tangents": 0.2,
        "informal": 0.15,
        "corrections": 0.1
    }
    
    # Normalize counts to densities/scores
    filler_score = min(quirk_data["fillers"]["density"] * 10, 1.0)
    hesitation_score = min(quirk_data["hesitations"]["total_hesitation_markers"] / 100, 1.0)
    tangent_score = min(quirk_data["tangents"]["total_tangents"] / 50, 1.0)
    informal_score = min(quirk_data["informal"]["density"], 1.0)
    correction_score = min(quirk_data["corrections"]["count"] / 20, 1.0)
    
    # Calculate weighted score
    total_score = (
        filler_score * weights["fillers"] +
        hesitation_score * weights["hesitations"] +
        tangent_score * weights["tangents"] +
        informal_score * weights["informal"] +
        correction_score * weights["corrections"]
    )
    
    return round(total_score, 6)


def run(input_string: str) -> Dict[str, Any]:
    """
    Interface function for the EchoScan pipeline.
    
    Args:
        input_string: Input string to analyze for human quirks
        
    Returns:
        Dict containing quirk analysis results
    """
    if not input_string.strip():
        return {
            "detector": "quirk_injection",
            "quirk_score": 0.0,
            "source_classification": "Unknown",
            "echo_score_modifier": 0.0,
            "advisory_flag": "QUIRK_INJECTION: Empty input"
        }
    
    # Detect different types of quirks
    fillers = detect_fillers(input_string)
    hesitations = detect_hesitations(input_string)
    tangents = detect_tangents(input_string)
    informal = detect_informal_language(input_string)
    corrections = detect_self_corrections(input_string)
    
    quirk_data = {
        "fillers": fillers,
        "hesitations": hesitations,
        "tangents": tangents,
        "informal": informal,
        "corrections": corrections
    }
    
    # Calculate overall quirk score
    quirk_score = calculate_quirk_score(quirk_data)
    
    # Determine authenticity based on quirk patterns
    text_length = len(input_string.split())
    
    if quirk_score < 0.05 and text_length > 50:
        # Very low quirk count in longer text is suspicious
        source_classification = "AI-Generated"
        echo_score_penalty = -8.0
        advisory_flag = "QUIRK_INJECTION: Suspiciously low human irregularities"
    elif quirk_score < 0.15 and text_length > 100:
        # Low quirk count in very long text
        source_classification = "Questionable"
        echo_score_penalty = -4.0
        advisory_flag = "QUIRK_INJECTION: Low human irregularity patterns"
    elif quirk_score > 0.6:
        # High quirk count suggests authentic human writing
        source_classification = "Human-Generated"
        echo_score_modifier = 6.0
        echo_score_penalty = 0.0
        advisory_flag = None
    elif quirk_score > 0.3:
        # Moderate quirk count
        source_classification = "Human-Generated"
        echo_score_modifier = 3.0
        echo_score_penalty = 0.0
        advisory_flag = None
    else:
        # Neutral or short text
        source_classification = "Unknown"
        echo_score_modifier = 0.0
        echo_score_penalty = 0.0
        advisory_flag = None
    
    # Compile results
    result = {
        "detector": "quirk_injection",
        "quirk_score": quirk_score,
        "source_classification": source_classification,
        "echo_score_modifier": locals().get("echo_score_modifier", 0.0),
        "echo_score_penalty": locals().get("echo_score_penalty", 0.0),
        "quirk_analysis": quirk_data,
        "text_length_words": text_length
    }
    
    if advisory_flag:
        result["advisory_flag"] = advisory_flag
    
    return result