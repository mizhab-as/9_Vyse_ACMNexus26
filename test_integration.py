#!/usr/bin/env python3
"""
NEXUS Integration Test Runner

Validates the entire system flow without real hardware:
1. Generates synthetic data
2. Runs through ML anomaly detector
3. Simulates backend LLM integration
4. Verifies alert generation

Usage: python test_integration.py
"""

import sys
import pandas as pd
import json
from datetime import datetime

sys.path.insert(0, 'ml_engine')
sys.path.insert(0, 'data_simulator')

from anomaly_detector import AnomalyDetector
from data_generator import RealisticAmbulanceDataSimulator

def generate_mock_triage_briefing(anomaly_score, alert_level, vitals):
    """Simulate LLM output without actual API call."""
    if alert_level == "CRITICAL":
        return f"Patient deteriorating rapidly. HR elevated to {vitals['heart_rate']} bpm, BP dropped to {vitals['systolic_bp']} mmHg. Suspect sepsis. Expedite ICU prep. Initiate sepsis protocol on arrival."
    elif alert_level == "WARNING":
        return f"Patient showing early concerning trends. Monitor closely during transport. Vitals trending unfavorably."
    else:
        return f"Patient stable. Continue standard monitoring."

def test_integration():
    print("[TEST] NEXUS Integration Test Starting")
    print("=" * 60)

    # Step 1: Generate synthetic data
    print("\n[STEP 1] Generating synthetic ambulance data...")
    simulator = RealisticAmbulanceDataSimulator(patient_id="TEST001", transport_minutes=45)
    df = simulator.generate_dataset()
    print(f"  Generated {len(df)} vitals samples (45 minutes)")

    # Step 2: Initialize ML detector
    print("\n[STEP 2] Initializing ML anomaly detector...")
    detector = AnomalyDetector(window_size=15, contamination=0.05)

    # Step 3: Process data
    print("\n[STEP 3] Processing data through ML pipeline...")
    alerts = []
    crisis_detected_at = None

    for idx, row in df.iterrows():
        vitals = {
            'heart_rate': row['heart_rate'],
            'systolic_bp': row['systolic_bp'],
            'diastolic_bp': row['diastolic_bp'],
            'respiratory_rate': row['respiratory_rate'],
            'oxygen_saturation': row['oxygen_saturation'],
            'temperature': row['temperature']
        }

        detected, score, details = detector.detect_anomaly(vitals)

        if detected and not crisis_detected_at:
            crisis_detected_at = idx
            alert_record = {
                'sample_idx': idx,
                'minute': row['minute_index'],
                'timestamp': row['timestamp'],
                'anomaly_score': float(score),
                'alert_level': details['alert_level'],
                'vitals': vitals,
                'triage_briefing': generate_mock_triage_briefing(score, details['alert_level'], vitals)
            }
            alerts.append(alert_record)

    # Step 4: Verify results
    print("\n[STEP 4] Verifying results...")
    print(f"  Total samples: {len(df)}")
    print(f"  Crisis detected: {'YES' if crisis_detected_at else 'NO'}")

    if crisis_detected_at:
        print(f"  Crisis at: Sample {crisis_detected_at} (minute {df.iloc[crisis_detected_at]['minute_index']:.1f})")
        print(f"  Timestamp: {df.iloc[crisis_detected_at]['timestamp']}")
        print()

        # Display first alert
        alert = alerts[0]
        print("  [ALERT BRIEFING]")
        print(f"    Anomaly Score: {alert['anomaly_score']:.2f}")
        print(f"    Alert Level: {alert['alert_level']}")
        print(f"    Vitals at alert:")
        print(f"      HR: {alert['vitals']['heart_rate']} bpm")
        print(f"      BP: {alert['vitals']['systolic_bp']}/{alert['vitals']['diastolic_bp']} mmHg")
        print(f"      RR: {alert['vitals']['respiratory_rate']}, O2: {alert['vitals']['oxygen_saturation']}%")
        print()
        print(f"    Pre-arrival Briefing:")
        print(f"      {alert['triage_briefing']}")

    # Step 5: Save test results
    print("\n[STEP 5] Saving test results...")
    with open('test_results.json', 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'total_samples': len(df),
            'crisis_detected': crisis_detected_at is not None,
            'crisis_at_minute': df.iloc[crisis_detected_at]['minute_index'] if crisis_detected_at else None,
            'first_alert': alerts[0] if alerts else None,
            'num_alerts': len(alerts)
        }, f, indent=2, default=str)

    print("  Results saved to test_results.json")

    # Step 6: Final status
    print("\n" + "=" * 60)
    if crisis_detected_at and len(alerts) > 0:
        print("[OK] INTEGRATION TEST PASSED")
        print(f"  Crisis detected at minute {df.iloc[crisis_detected_at]['minute_index']:.1f}")
        print(f"  Pre-arrival briefing generated successfully")
    else:
        print("[FAIL] INTEGRATION TEST FAILED - No alerts generated")
        return False

    return True

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
