import asyncio
import random
from typing import AsyncGenerator, Dict

async def simulate_ambulance_ride() -> AsyncGenerator[Dict, None]:
    """
    Simulates a 45-minute transit over 45 seconds (1 hz).
    Phases:
      0-15s: Stable
      16-30s: Early Deterioration (rising HR, slight BP drop)
      31-45s: Septic Shock (Tachycardia, Hypotension)
    """
    minute_counter = 0
    # Baseline normal vitals
    hr_base = 75
    systolic_base = 120
    oxygen_base = 98

    while True:
        minute_counter += 1
        
        # Add random noise
        hr = hr_base + random.randint(-2, 2)
        systolic = systolic_base + random.randint(-4, 4)
        oxygen = oxygen_base + random.randint(-1, 0)
        
        # Phase 2: Deterioration (minutes 16 - 30)
        if 15 < minute_counter <= 30:
            hr_base += random.uniform(1, 3) # Heart rate climbing
            systolic_base -= random.uniform(1, 2.5) # BP dropping
            if random.random() > 0.5:
                oxygen_base -= 1 # Occasional O2 drop
                
        # Phase 3: Critical cascade (minutes 31 - 45)
        elif 30 < minute_counter:
            hr_base += random.uniform(2, 5) # Severe tachycardia
            systolic_base -= random.uniform(2, 4) # Severe hypotension
            oxygen_base -= random.uniform(0.5, 1.5)
            
        # Hard limits
        hr = max(30, min(hr, 220))
        systolic = max(40, min(systolic, 200))
        oxygen = max(60, min(oxygen, 100))

        vitals = {
            "timestamp": minute_counter,
            "heart_rate": int(hr),
            "blood_pressure": int(systolic),
            "oxygen_saturation": int(oxygen),
            "status": "Green" if minute_counter <= 15 else ("Yellow" if minute_counter <= 30 else "Red")
        }
        
        yield vitals
        await asyncio.sleep(1) # Send 1 mock "minute" (45min total transit) per second
