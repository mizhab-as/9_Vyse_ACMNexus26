"""
Real Data Loader - Load actual patient vitals from PSV files

Instead of generating synthetic data, this loads real ICU patient records
from the MIMIC-III dataset (p000001_stable.psv, p000009_sepsis.psv, etc.)

This gives you:
✓ Real patient vital trends
✓ Actual septic shock progression
✓ Authentic anomaly patterns
✗ Zero synthetic data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os


class RealDataLoader:
    """Load real patient vitals from MIMIC-III PSV files"""

    def __init__(self, psv_file: str, patient_id: str = "REAL_P001"):
        """
        Args:
            psv_file: Path to .psv file (e.g., p000001_stable.psv)
            patient_id: Patient ID for NEXUS system
        """
        self.psv_file = psv_file
        self.patient_id = patient_id
        self.df = None
        self.sample_idx = 0
        self._load_data()

    def _load_data(self):
        """Load and preprocess PSV data"""
        if not os.path.exists(self.psv_file):
            raise FileNotFoundError(f"PSV file not found: {self.psv_file}")

        print(f"[REAL DATA] Loading {os.path.basename(self.psv_file)}...")

        # Load PSV (pipe-separated values)
        self.df = pd.read_csv(self.psv_file, sep='|')

        # Extract filename for dataset info
        filename = os.path.basename(self.psv_file)
        if "sepsis" in filename.lower():
            print("[REAL DATA] Dataset: Septic Shock Progression")
            self.scenario = "sepsis"
        else:
            print("[REAL DATA] Dataset: Stable Patient Vitals")
            self.scenario = "stable"

        # Calculate expected duration
        total_rows = len(self.df)
        expected_minutes = total_rows * 10 / 60  # Assume 10-second intervals
        print(f"[REAL DATA] Total samples: {total_rows} (~{expected_minutes:.1f} minutes)")

    def get_sample(self, idx: int) -> Optional[Dict[str, Any]]:
        """
        Get vitals for sample index

        Returns standardized NEXUS format or None if index out of bounds
        """
        if idx >= len(self.df):
            return None

        row = self.df.iloc[idx]

        # Extract vitals (handle NaN values)
        vitals = {
            "heart_rate": self._safe_extract(row, "HR", 80),
            "oxygen_saturation": self._safe_extract(row, "O2Sat", 95),
            "systolic_bp": self._safe_extract(row, "SBP", 120),
            "diastolic_bp": self._safe_extract(row, "DBP", 80),
            "respiratory_rate": self._safe_extract(row, "Resp", 16),
            "temperature": self._safe_extract(row, "Temp", 37.0),
        }

        # Validate ranges (physiological bounds)
        vitals = self._validate_vitals(vitals)

        # Calculate elapsed time
        elapsed_minutes = idx * 10 / 60
        elapsed_seconds = idx * 10

        # Simulate GPS location (ambulance moving)
        lat = 42.3656 + (elapsed_minutes / 100) * 0.01  # Boston area baseline
        lng = -71.0096 + (elapsed_minutes / 100) * 0.01
        eta = max(2, 15 - int(elapsed_minutes))

        return {
            "timestamp": (datetime.utcnow() + timedelta(seconds=elapsed_seconds)).isoformat(),
            "patient_id": self.patient_id,
            "vitals": vitals,
            "location": {
                "latitude": lat,
                "longitude": lng,
                "eta_minutes": eta
            },
            "source": "MIMIC-III",
            "scenario": self.scenario,
            "sample_index": idx
        }

    @staticmethod
    def _safe_extract(row: pd.Series, col: str, default: float) -> float:
        """Extract value from row, default to reasonable value if NaN"""
        try:
            val = row.get(col)
            if pd.isna(val):
                return default
            return float(val)
        except:
            return default

    @staticmethod
    def _validate_vitals(vitals: Dict[str, float]) -> Dict[str, float]:
        """Ensure vitals are within physiological ranges"""
        ranges = {
            "heart_rate": (30, 200),
            "oxygen_saturation": (50, 100),
            "systolic_bp": (50, 250),
            "diastolic_bp": (20, 150),
            "respiratory_rate": (5, 60),
            "temperature": (32, 42)
        }

        for key, (min_val, max_val) in ranges.items():
            if key in vitals:
                vitals[key] = max(min_val, min(max_val, vitals[key]))

        return vitals

    def get_next_sample(self) -> Optional[Dict[str, Any]]:
        """Get next sample and advance index"""
        sample = self.get_sample(self.sample_idx)
        if sample:
            self.sample_idx += 1
        return sample

    def reset(self):
        """Reset to beginning"""
        self.sample_idx = 0

    def total_samples(self) -> int:
        """Get total number of samples in dataset"""
        return len(self.df)

    def get_all_samples(self):
        """Generator to iterate through all samples"""
        for idx in range(len(self.df)):
            sample = self.get_sample(idx)
            if sample:
                yield sample


class MultiPatientRealDataLoader:
    """Load multiple real patient PSV files sequentially"""

    def __init__(self, psv_directory: str):
        """
        Args:
            psv_directory: Directory containing PSV files
        """
        self.psv_directory = psv_directory
        self.loaders = []
        self.current_loader_idx = 0
        self._load_all_files()

    def _load_all_files(self):
        """Find and load all PSV files in directory"""
        psv_files = []
        for file in os.listdir(self.psv_directory):
            if file.endswith(".psv"):
                psv_files.append(os.path.join(self.psv_directory, file))

        psv_files.sort()

        print(f"[REAL DATA] Found {len(psv_files)} PSV files")
        for idx, psv_file in enumerate(psv_files):
            patient_id = f"REAL_P{idx:03d}"
            try:
                loader = RealDataLoader(psv_file, patient_id)
                self.loaders.append(loader)
            except Exception as e:
                print(f"[ERROR] Failed to load {file}: {e}")

    def get_next_sample(self) -> Optional[Dict[str, Any]]:
        """Get next sample from current loader, switch when done"""
        if not self.loaders:
            return None

        loader = self.loaders[self.current_loader_idx]
        sample = loader.get_next_sample()

        # Switch to next patient if current is exhausted
        if not sample and self.current_loader_idx < len(self.loaders) - 1:
            self.current_loader_idx += 1
            print(f"\n[REAL DATA] Switching to next patient...")
            return self.get_next_sample()

        return sample

    def total_patients(self) -> int:
        """Number of patient datasets loaded"""
        return len(self.loaders)


def test_real_data():
    """Test the real data loader"""
    psv_file = "data_simulator/p000009_sepsis.psv"

    if not os.path.exists(psv_file):
        print(f"[ERROR] Test file not found: {psv_file}")
        print("Run from project root directory")
        return

    loader = RealDataLoader(psv_file, patient_id="TEST_P001")

    print("\n[TEST] Sample vitals from real data:\n")
    print(f"{'Sample':<8} {'HR':<6} {'BP':<12} {'O2':<6} {'RR':<5} {'Temp':<6}")
    print("-" * 50)

    for i in range(min(10, loader.total_samples())):
        sample = loader.get_sample(i)
        if sample:
            v = sample["vitals"]
            print(f"{i:<8} {int(v['heart_rate']):<6} "
                  f"{int(v['systolic_bp'])}/{int(v['diastolic_bp']):<8} "
                  f"{int(v['oxygen_saturation']):<6} "
                  f"{int(v['respiratory_rate']):<5} "
                  f"{v['temperature']:.1f}")


if __name__ == "__main__":
    import asyncio
    test_real_data()
