# shadow_fseq_monitor.py — Production Integration Version
"""
Shadow F-SEQ Monitor for Ashby-Vira v3.2
Connects to: semantic_immune_system.py + api_server.py
Purpose: Run Bayesian/Popperian tracks in parallel, log divergence
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Tuple, Optional
from enum import Enum

# ============================================================================
# CONFIGURATION
# ============================================================================

SHADOW_LOG_FILE = "shadow_fseq_logs.json"
DIVERGENCE_THRESHOLD = 0.35
HIGH_PRIOR_THRESHOLD = 4.0
LOW_PRIOR_THRESHOLD = 3.0

# ============================================================================
# SEVERITY (Matches your semantic_immune_system.py)
# ============================================================================

class TrackSeverity(Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FROZEN = "FROZEN"

# Map immune system severity to numeric effect strength
SEVERITY_EFFECT_MAP = {
    TrackSeverity.HEALTHY: 0.10,
    TrackSeverity.WARNING: 0.25,
    TrackSeverity.CRITICAL: 0.40,
    TrackSeverity.FROZEN: 0.50,
}

# ============================================================================
# BAYESIAN TRACK — Uses health score as prior (trust-weighted)
# ============================================================================

class BayesianTrack:
    """
    Bayesian inference using system health score as prior.
    High health = high confidence (prior is informative)
    Low health = low confidence (prior says something is wrong)
    """

    def evaluate(self, health_score: float, severity: TrackSeverity) -> Tuple[float, str]:
        """
        Input: health_score (0-100), severity level
        Output: (confidence_score 0-1, decision ALLOW/BLOCK)
        """
        # Normalize health score to 0-1
        prior_strength = health_score / 100.0

        # Effect strength from severity
        effect = SEVERITY_EFFECT_MAP.get(severity, 0.25)

        # Bayesian confidence: prior dominates when strong, effect adjusts
        # High health + low severity = high confidence (ALLOW)
        # Low health + high severity = low confidence (BLOCK)
        confidence = prior_strength - (effect * 0.5)
        confidence = max(0.1, min(0.95, confidence))

        decision = "ALLOW" if confidence >= 0.65 else "BLOCK"
        return round(confidence, 3), decision

# ============================================================================
# POPPERIAN TRACK — Ignores health score, tests evidence severity only
# ============================================================================

class PopperianTrack:
    """
    Popperian corroboration — evaluates evidence severity WITHOUT
    trusting the health score prior.
    """

    def evaluate(self, severity: TrackSeverity, drift_detected: bool) -> Tuple[float, str]:
        """
        Input: severity level, whether drift was detected
        Output: (corroboration_score 0-1, decision ALLOW/BLOCK)
        """
        effect = SEVERITY_EFFECT_MAP.get(severity, 0.25)

        # Popperian: How surprising is this evidence?
        # High severity + drift = strong evidence against system stability
        if drift_detected:
            # Drift makes evidence more severe (surprising)
            corroboration = 0.3 + (effect * 0.8)
        else:
            # No drift — evidence is less surprising
            corroboration = 0.5 + (effect * 0.5)

        corroboration = max(0.1, min(0.95, corroboration))

        # Popperian is stricter — higher threshold to allow
        decision = "ALLOW" if corroboration >= 0.75 else "BLOCK"
        return round(corroboration, 3), decision

# ============================================================================
# MAIN MONITOR CLASS
# ============================================================================

class ShadowFSeqMonitor:

    def __init__(self):
        self.bayesian_track = BayesianTrack()
        self.popperian_track = PopperianTrack()
        self.log_entries = []

    def compute_prior_informativeness(self, health_score: float, effect_estimate: float) -> float:
        """
        D(H) from F-SEQ paper, adapted:
        - health_score normalized to 0-1
        - Measures how far from neutral (0.5) the prior is
        - Divided by effect strength
        """
        epsilon = 0.01
        prior_normalized = health_score / 100.0
        return abs(prior_normalized - 0.5) / max(abs(effect_estimate), epsilon)

    def evaluate_validation_event(
        self,
        intervention: str,
        health_score: float,
        severity_str: str,
        drift_detected: bool,
        validation_status: str
    ) -> Dict[str, Any]:
        """
        Main evaluation — called from api_server.py /validate endpoint.

        Args:
            intervention: The intervention string being validated
            health_score: From immune_system.run_diagnostic().health_score (0-100)
            severity_str: From immune_system diagnostic ("HEALTHY"/"WARNING"/etc)
            drift_detected: From immune_system.detect_drift() (True/False)
            validation_status: What Vira actually decided (for comparison)
        """
        # Parse severity
        try:
            severity = TrackSeverity(severity_str)
        except ValueError:
            severity = TrackSeverity.HEALTHY

        # Effect estimate from severity
        effect_estimate = SEVERITY_EFFECT_MAP.get(severity, 0.25)

        # Run both tracks
        bayes_score, bayes_decision = self.bayesian_track.evaluate(health_score, severity)
        popper_score, popper_decision = self.popperian_track.evaluate(severity, drift_detected)

        # Divergence
        divergence = abs(bayes_score - popper_score)

        # Prior informativeness
        d_h = self.compute_prior_informativeness(health_score, effect_estimate)

        if d_h > HIGH_PRIOR_THRESHOLD:
            trusted_track = "BAYESIAN"
        elif d_h < LOW_PRIOR_THRESHOLD:
            trusted_track = "POPPERIAN"
        else:
            trusted_track = "AMBIGUOUS"

        tracks_disagree = (bayes_decision != popper_decision)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_id": f"val_{len(self.log_entries)}",
            "intervention_hash": hash(intervention) % 10000,
            "health_score": round(health_score, 2),
            "severity": severity_str,
            "drift_detected": drift_detected,
            "effect_estimate": round(effect_estimate, 3),
            "d_h_score": round(d_h, 3),
            "bayesian": {"score": bayes_score, "decision": bayes_decision},
            "popperian": {"score": popper_score, "decision": popper_decision},
            "divergence": round(divergence, 3),
            "tracks_disagree": tracks_disagree,
            "trusted_track": trusted_track,
            "frozen_trigger": (tracks_disagree and divergence > DIVERGENCE_THRESHOLD),
            "vira_actual_decision": validation_status,
            "shadow_matches_vira": (
                (bayes_decision == "ALLOW" and validation_status == "VALID") or
                (bayes_decision == "BLOCK" and validation_status != "VALID")
            )
        }

        self.log_entries.append(log_entry)
        return log_entry

    def save_logs(self, filepath: str = SHADOW_LOG_FILE):
        with open(filepath, 'w') as f:
            json.dump(self.log_entries, f, indent=2)
        print(f"✓ Saved {len(self.log_entries)} log entries to {filepath}")

    def load_existing_logs(self, filepath: str = SHADOW_LOG_FILE):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.log_entries = json.load(f)
            print(f"✓ Loaded {len(self.log_entries)} existing log entries")
        else:
            print("ℹ No existing logs found - starting fresh")

    def generate_calibration_report(self):
        if not self.log_entries:
            print("No log data available.")
            return

        total = len(self.log_entries)
        disagreements = sum(1 for l in self.log_entries if l['tracks_disagree'])
        frozen = sum(1 for l in self.log_entries if l['frozen_trigger'])
        matches = sum(1 for l in self.log_entries if l.get('shadow_matches_vira', False))

        d_scores = [l['d_h_score'] for l in self.log_entries]
        bayes_count = sum(1 for l in self.log_entries if l['trusted_track'] == 'BAYESIAN')
        popper_count = sum(1 for l in self.log_entries if l['trusted_track'] == 'POPPERIAN')
        ambig_count = sum(1 for l in self.log_entries if l['trusted_track'] == 'AMBIGUOUS')

        print("\n" + "=" * 60)
        print("       F-SEQ SHADOW MONITOR CALIBRATION REPORT")
        print("=" * 60)
        print(f"\nTotal validation events: {total}")
        print(f"Track disagreements: {disagreements} ({100*disagreements/total:.1f}%)")
        print(f"FROZEN triggers: {frozen} ({100*frozen/total:.1f}%)")
        print(f"Shadow matches Vira: {matches}/{total} ({100*matches/total:.1f}%)")
        print(f"\nD(H) Distribution:")
        print(f"  Min: {min(d_scores):.3f}, Max: {max(d_scores):.3f}, Median: {sorted(d_scores)[total//2]:.3f}")
        print(f"\nTrack Usage:")
        print(f"  Bayesian (D>{HIGH_PRIOR_THRESHOLD}): {bayes_count} ({100*bayes_count/total:.1f}%)")
        print(f"  Popperian (D<{LOW_PRIOR_THRESHOLD}): {popper_count} ({100*popper_count/total:.1f}%)")
        print(f"  Ambiguous: {ambig_count} ({100*ambig_count/total:.1f}%)")

        # Drift analysis
        drift_events = [l for l in self.log_entries if l.get('drift_detected', False)]
        if drift_events:
            drift_disagree = sum(1 for l in drift_events if l['tracks_disagree'])
            print(f"\nDrift Events: {len(drift_events)}")
            print(f"  Disagreements during drift: {drift_disagree}/{len(drift_events)}")

        print(f"\nRecommendations:")
        if frozen / total > 0.10:
            print(f"  ⚠️  Frozen rate high. Raise DIVERGENCE_THRESHOLD to 0.40")
        if disagreements / total < 0.05:
            print(f"  ℹ️  Low disagreement. Lower DIVERGENCE_THRESHOLD to 0.25")
        if matches / total < 0.50:
            print(f"  ⚠️  Shadow rarely matches Vira. Review threshold calibration")
        print("=" * 60 + "\n")

# ============================================================================
# SINGLETON FOR API SERVER IMPORT
# ============================================================================

shadow_monitor = ShadowFSeqMonitor()