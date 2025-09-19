"""Enhanced Motif detector module for EchoScan with EchoFold + SDS-1 DNA arcs."""

import numpy as np
from typing import Dict, List, Any, Tuple


def detect_loop_recursion(stream: str) -> Dict[str, Any]:
    """Detect loop recursion patterns in the input stream."""
    if len(stream) < 6:
        return {"loop_detected": False, "recursion_depth": 0, "pattern_length": 0}
    
    max_recursion = 0
    detected_pattern = ""
    
    # Look for patterns of various lengths
    for pattern_len in range(2, min(len(stream) // 3, 20)):
        for start in range(len(stream) - pattern_len):
            pattern = stream[start:start + pattern_len]
            recursion_count = 1
            pos = start + pattern_len
            
            # Count consecutive repetitions
            while pos + pattern_len <= len(stream) and stream[pos:pos + pattern_len] == pattern:
                recursion_count += 1
                pos += pattern_len
            
            if recursion_count > max_recursion:
                max_recursion = recursion_count
                detected_pattern = pattern
    
    return {
        "loop_detected": max_recursion >= 3,
        "recursion_depth": max_recursion,
        "pattern_length": len(detected_pattern),
        "detected_pattern": detected_pattern[:10] + "..." if len(detected_pattern) > 10 else detected_pattern
    }


def detect_missing_closures(stream: str) -> Dict[str, Any]:
    """Detect missing closures in bracketed structures."""
    brackets = {'(': ')', '[': ']', '{': '}', '<': '>'}
    stack = []
    unmatched_opens = 0
    unmatched_closes = 0
    
    for char in stream:
        if char in brackets:
            stack.append(char)
        elif char in brackets.values():
            if stack:
                last_open = stack.pop()
                if brackets.get(last_open) != char:
                    unmatched_closes += 1
            else:
                unmatched_closes += 1
    
    unmatched_opens = len(stack)
    total_unmatched = unmatched_opens + unmatched_closes
    
    return {
        "missing_closures": total_unmatched > 0,
        "unmatched_opens": unmatched_opens,
        "unmatched_closes": unmatched_closes,
        "closure_ratio": 1.0 - (total_unmatched / max(1, len([c for c in stream if c in '()[]{}<>'])))
    }


def detect_parasite_glyphs(stream: str) -> Dict[str, Any]:
    """Detect parasite glyphs - unusual character patterns that might indicate synthetic content."""
    
    # Define suspicious patterns
    suspicious_patterns = [
        # Unusual Unicode ranges
        lambda c: ord(c) > 127 and ord(c) < 160,  # Control characters
        lambda c: ord(c) > 8191 and ord(c) < 8208,  # General punctuation
        lambda c: ord(c) > 65279,  # High Unicode ranges
        # Repeated non-standard spacing
        lambda c: c in '\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A',
        # Zero-width characters
        lambda c: c in '\u200B\u200C\u200D\u2060\uFEFF'
    ]
    
    parasite_count = 0
    total_chars = len(stream)
    parasite_positions = []
    
    for i, char in enumerate(stream):
        for pattern_func in suspicious_patterns:
            if pattern_func(char):
                parasite_count += 1
                parasite_positions.append(i)
                break
    
    # Calculate distribution of parasites
    distribution_variance = 0.0
    if len(parasite_positions) > 1:
        gaps = [parasite_positions[i] - parasite_positions[i-1] for i in range(1, len(parasite_positions))]
        distribution_variance = np.var(gaps) if gaps else 0.0
    
    return {
        "parasite_detected": parasite_count > 0,
        "parasite_count": parasite_count,
        "parasite_ratio": parasite_count / max(1, total_chars),
        "distribution_variance": distribution_variance,
        "clustered_parasites": distribution_variance < 10.0 if parasite_count > 2 else False
    }


def calculate_sds1_dna_arcs(stream: str) -> Dict[str, Any]:
    """Calculate SDS-1 DNA-style arcs for pattern analysis."""
    
    # Convert text to DNA-like sequence (A, T, G, C based on character properties)
    dna_mapping = {
        'vowels': 'A',      # A, E, I, O, U
        'consonants': 'T',   # Most consonants
        'digits': 'G',       # 0-9
        'special': 'C'       # Punctuation, spaces, etc.
    }
    
    dna_sequence = ""
    for char in stream.lower():
        if char in 'aeiou':
            dna_sequence += 'A'
        elif char.isalpha():
            dna_sequence += 'T'
        elif char.isdigit():
            dna_sequence += 'G'
        else:
            dna_sequence += 'C'
    
    # Analyze arcs (complementary base pairing patterns)
    arc_patterns = []
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    
    for i in range(len(dna_sequence)):
        for j in range(i + 3, min(i + 50, len(dna_sequence))):  # Look ahead 3-50 positions
            if dna_sequence[i] == complement.get(dna_sequence[j], ''):
                arc_length = j - i
                arc_patterns.append({
                    'start': i,
                    'end': j,
                    'length': arc_length,
                    'base_pair': f"{dna_sequence[i]}-{dna_sequence[j]}"
                })
    
    # Calculate arc statistics
    arc_count = len(arc_patterns)
    avg_arc_length = np.mean([arc['length'] for arc in arc_patterns]) if arc_patterns else 0.0
    arc_density = arc_count / max(1, len(dna_sequence))
    
    return {
        "dna_sequence": dna_sequence[:50] + "..." if len(dna_sequence) > 50 else dna_sequence,
        "arc_count": arc_count,
        "average_arc_length": round(avg_arc_length, 2),
        "arc_density": round(arc_density, 4),
        "complementarity_score": min(1.0, arc_density * 2),  # Normalize to 0-1
        "dominant_base": max('ATGC', key=dna_sequence.count) if dna_sequence else 'A'
    }


def run(stream: str) -> Dict[str, Any]:
    """Enhanced motif detection with loop recursion, missing closures, and parasite glyphs."""
    
    if len(stream) == 0:
        return {
            "detector": "motif_enhanced",
            "top_motif": "",
            "repeat_score": 0.0,
            "delta_s": 0.0,
            "echo_score_modifier": 0.0,
            "loop_recursion": {"loop_detected": False, "recursion_depth": 0},
            "missing_closures": {"missing_closures": False, "unmatched_opens": 0},
            "parasite_glyphs": {"parasite_detected": False, "parasite_count": 0},
            "sds1_dna_arcs": {"arc_count": 0, "complementarity_score": 0.0}
        }
    
    # Original motif detection
    ascii_vals = np.array([ord(c) for c in stream])
    motifs = {}
    for i in range(len(stream)-2):
        motif = stream[i:i+3]
        motifs[motif] = motifs.get(motif, 0) + 1
    top_motif = max(motifs, key=motifs.get) if motifs else ""
    repeat_score = motifs[top_motif] / len(stream) if motifs and len(stream) > 0 else 0.0
    
    # Enhanced drift stability calculation
    def digit_sum(n, base): 
        return sum(int(d) for d in np.base_repr(n, base))
    
    drift_vals = []
    for b in [6, 7, 8, 9]:
        digit_sums = [digit_sum(v, b) for v in ascii_vals]
        if len(digit_sums) > 1:
            drift_vals.append(np.mean(np.abs(np.diff(digit_sums))))
        else:
            drift_vals.append(0.0)
    delta_s = float(np.mean(drift_vals)) if drift_vals else 0.0
    
    # Enhanced pattern detection
    loop_analysis = detect_loop_recursion(stream)
    closure_analysis = detect_missing_closures(stream)
    parasite_analysis = detect_parasite_glyphs(stream)
    dna_arc_analysis = calculate_sds1_dna_arcs(stream)
    
    # Calculate enhanced echo score modifier with new factors
    base_modifier = max(0.1, 1 - delta_s) * repeat_score
    loop_penalty = -0.2 if loop_analysis["recursion_depth"] > 5 else 0.0
    closure_penalty = -0.1 * (1.0 - closure_analysis["closure_ratio"])
    parasite_penalty = -0.3 * parasite_analysis["parasite_ratio"]
    arc_bonus = 0.1 * dna_arc_analysis["complementarity_score"]
    
    enhanced_modifier = base_modifier + loop_penalty + closure_penalty + parasite_penalty + arc_bonus
    
    return {
        "detector": "motif_enhanced",
        "top_motif": top_motif,
        "repeat_score": round(repeat_score, 3),
        "delta_s": round(delta_s, 6),
        "echo_score_modifier": round(enhanced_modifier, 3),
        "loop_recursion": loop_analysis,
        "missing_closures": closure_analysis,
        "parasite_glyphs": parasite_analysis,
        "sds1_dna_arcs": dna_arc_analysis,
        "pattern_complexity": {
            "motif_diversity": len(motifs),
            "max_motif_frequency": max(motifs.values()) if motifs else 0,
            "entropy": -sum((count/len(stream)) * np.log2(count/len(stream)) 
                          for count in motifs.values() if count > 0) if motifs else 0.0
        }
    }