import time
import random
import datetime

# --- Simulation Constants ---
SIMULATION_DURATION_MINUTES = 45
STABLE_DURATION_MINUTES = 30
SECONDS_PER_MINUTE = 60

# --- Vitals Constants ---
STABLE_SPO2 = 98.0
STABLE_HR = 80.0
FINAL_SPO2 = 85.0
FINAL_HR = 130.0

# Noise factor to simulate motion artifacts
SPO2_NOISE = 0.5
HR_NOISE = 2.0

def stream_vitals():
    """
    A generator function that simulates and yields patient vitals (SpO2 and HR)
    every second for a total of 45 minutes.
    
    - First 30 minutes: Vitals are stable with random noise.
    - Last 15 minutes: Vitals show a gradual, linear deterioration.
    """
    total_seconds = SIMULATION_DURATION_MINUTES * SECONDS_PER_MINUTE
    stable_seconds = STABLE_DURATION_MINUTES * SECONDS_PER_MINUTE
    deterioration_seconds = total_seconds - stable_seconds

    # Calculate the rate of change per second for the deterioration phase
    spo2_drop_per_second = (STABLE_SPO2 - FINAL_SPO2) / deterioration_seconds
    hr_increase_per_second = (FINAL_HR - STABLE_HR) / deterioration_seconds

    print(f"Starting {SIMULATION_DURATION_MINUTES}-minute vital sign simulation...")
    print(f"Stable phase for {STABLE_DURATION_MINUTES} minutes, then deterioration.")

    for second in range(total_seconds):
        timestamp = datetime.datetime.now().isoformat()
        
        if second < stable_seconds:
            # --- Stable Phase ---
            current_spo2 = STABLE_SPO2 + random.uniform(-SPO2_NOISE, SPO2_NOISE)
            current_hr = STABLE_HR + random.uniform(-HR_NOISE, HR_NOISE)
        else:
            # --- Deterioration Phase ---
            seconds_into_deterioration = second - stable_seconds
            
            spo2_drop = spo2_drop_per_second * seconds_into_deterioration
            hr_increase = hr_increase_per_second * seconds_into_deterioration
            
            current_spo2 = (STABLE_SPO2 - spo2_drop) + random.uniform(-SPO2_NOISE, SPO2_NOISE)
            current_hr = (STABLE_HR + hr_increase) + random.uniform(-HR_NOISE, HR_NOISE)

        # Yield the data as a dictionary
        yield {
            "timestamp": timestamp,
            "SpO2": round(max(0, min(100, current_spo2)), 2),
            "HR": round(max(0, current_hr), 2)
        }
        
        # Simulate 1-second interval
        time.sleep(1)

if __name__ == "__main__":
    # Example of how to use the generator
    vital_stream = stream_vitals()
    
    try:
        for vital_data in vital_stream:
            print(f"Timestamp: {vital_data['timestamp']}, SpO2: {vital_data['SpO2']}%, HR: {vital_data['HR']} bpm")
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")