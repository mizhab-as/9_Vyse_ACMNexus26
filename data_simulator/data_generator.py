import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class RealisticAmbulanceDataSimulator:
    """
    Generates a realistic 45-minute ambulance transit dataset.

    Scenario: Patient starts with normal vitals, then deteriorates
    into septic shock over the transport period.

    Septic Shock Progression (realistic):
    - Minutes 0-5: Baseline normal vitals
    - Minutes 5-15: Early signs (subtle fever, slight tachycardia)
    - Minutes 15-30: Progressive deterioration (BP drops, HR increases, RR increases)
    - Minutes 30-45: Septic shock crisis (hypotension, severe tachycardia, altered O2)
    """

    def __init__(self, patient_id: str = "P001", transport_minutes: int = 45, sample_interval_seconds: int = 10):
        self.patient_id = patient_id
        self.transport_minutes = transport_minutes
        self.sample_interval_seconds = sample_interval_seconds
        self.total_samples = (transport_minutes * 60) // sample_interval_seconds

    def generate_baseline_vitals(self) -> dict:
        """Normal adult vitals at baseline."""
        return {
            "heart_rate": 72,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "respiratory_rate": 16,
            "oxygen_saturation": 98,
            "temperature": 37.0
        }

    def get_deterioration_factor(self, minute: int) -> float:
        """
        Computes deterioration intensity as a function of time.
        Follows a sigmoid-like curve (slow start, rapid middle, plateau end).

        0-5 min: 0.0 (normal)
        5-15 min: 0.0-0.3 (early signs)
        15-30 min: 0.3-0.8 (progressive)
        30-45 min: 0.8-1.0 (crisis)
        """
        if minute < 5:
            return 0.0
        elif minute < 15:
            return (minute - 5) / 10 * 0.3  # 0 to 0.3
        elif minute < 30:
            return 0.3 + (minute - 15) / 15 * 0.5  # 0.3 to 0.8
        else:
            return 0.8 + (minute - 30) / 15 * 0.2  # 0.8 to 1.0

    def simulate_vitals_at_minute(self, minute: int, baseline: dict) -> dict:
        """
        Generates vitals at a specific minute with physiologically realistic variation.
        """
        deterioration = self.get_deterioration_factor(minute)

        # Small random variation (noise)
        noise = {
            "hr": np.random.normal(0, 2),
            "sbp": np.random.normal(0, 3),
            "dbp": np.random.normal(0, 2),
            "rr": np.random.normal(0, 0.5),
            "spo2": np.random.normal(0, 1),
            "temp": np.random.normal(0, 0.1),
        }

        # Apply deterioration changes
        vitals = {
            "heart_rate": int(baseline["heart_rate"] + (30 * deterioration) + noise["hr"]),
            "systolic_bp": int(baseline["systolic_bp"] - (30 * deterioration) + noise["sbp"]),
            "diastolic_bp": int(baseline["diastolic_bp"] - (15 * deterioration) + noise["dbp"]),
            "respiratory_rate": int(baseline["respiratory_rate"] + (12 * deterioration) + noise["rr"]),
            "oxygen_saturation": int(baseline["oxygen_saturation"] - (8 * deterioration) + noise["spo2"]),
            "temperature": baseline["temperature"] + (1.5 * deterioration) + noise["temp"],
        }

        # Enforce realistic bounds
        vitals["heart_rate"] = max(40, min(160, vitals["heart_rate"]))
        vitals["systolic_bp"] = max(70, min(180, vitals["systolic_bp"]))
        vitals["diastolic_bp"] = max(40, min(110, vitals["diastolic_bp"]))
        vitals["respiratory_rate"] = max(8, min(35, vitals["respiratory_rate"]))
        vitals["oxygen_saturation"] = max(85, min(100, vitals["oxygen_saturation"]))
        vitals["temperature"] = max(35.0, min(40.0, vitals["temperature"]))

        return vitals

    def generate_dataset(self) -> pd.DataFrame:
        """
        Generates complete 45-minute ambulance dataset.
        Returns DataFrame with columns: timestamp, patient_id, and all vitals.
        """
        baseline = self.generate_baseline_vitals()
        start_time = datetime(2026, 3, 27, 14, 30, 0)

        data = []
        for sample_idx in range(self.total_samples):
            timestamp = start_time + timedelta(seconds=sample_idx * self.sample_interval_seconds)
            minute = (sample_idx * self.sample_interval_seconds) / 60.0

            vitals = self.simulate_vitals_at_minute(minute, baseline)

            row = {
                "timestamp": timestamp.isoformat() + "Z",
                "patient_id": self.patient_id,
                "minute_index": minute,
                **vitals
            }
            data.append(row)

        df = pd.DataFrame(data)
        return df

    def save_to_csv(self, filename: str = "ambulance_vitals.csv") -> str:
        """Generates and saves dataset to CSV."""
        df = self.generate_dataset()
        df.to_csv(filename, index=False)
        print(f"[OK] Generated {len(df)} samples in {filename}")
        print(f"[INFO] Time span: {df['minute_index'].min():.1f} to {df['minute_index'].max():.1f} minutes")
        print(f"[INFO] HR range: {df['heart_rate'].min()}-{df['heart_rate'].max()} bpm")
        print(f"[INFO] SBP range: {df['systolic_bp'].min()}-{df['systolic_bp'].max()} mmHg")
        return filename

    def get_sample_for_streaming(self, sample_idx: int) -> dict:
        """
        Returns a single vitals sample in the JSON format expected by backend.
        Use this for streaming simulation.
        """
        baseline = self.generate_baseline_vitals()
        minute = (sample_idx * self.sample_interval_seconds) / 60.0
        vitals = self.simulate_vitals_at_minute(minute, baseline)
        timestamp = datetime(2026, 3, 27, 14, 30, 0) + timedelta(seconds=sample_idx * self.sample_interval_seconds)

        return {
            "timestamp": timestamp.isoformat() + "Z",
            "patient_id": self.patient_id,
            "vitals": vitals,
            "location": {
                "latitude": 12.9352 + (np.random.random() * 0.001),
                "longitude": 77.6245 + (np.random.random() * 0.001),
                "eta_minutes": max(1, int((self.transport_minutes * 60 - (sample_idx * self.sample_interval_seconds)) / 60))
            }
        }


# ============== Main execution ==============

if __name__ == "__main__":
    print("[NEXUS] Generating realistic ambulance transit dataset...")
    simulator = RealisticAmbulanceDataSimulator(patient_id="P001", transport_minutes=45)

    # Generate and save CSV
    csv_file = simulator.save_to_csv("ambulance_vitals_45min.csv")

    # Display sample data
    print("\n[DATA] Sample data (first 5 minutes):")
    df = pd.read_csv(csv_file)
    print(df[df['minute_index'] <= 5][['timestamp', 'heart_rate', 'systolic_bp', 'respiratory_rate', 'oxygen_saturation']].head(30))

    print("\n[DATA] Sample data (crisis phase, 30+ minutes):")
    print(df[df['minute_index'] >= 30][['timestamp', 'heart_rate', 'systolic_bp', 'respiratory_rate', 'oxygen_saturation']].tail(15))

    print(f"\n[OK] Dataset ready: {csv_file}")
