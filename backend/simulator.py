import asyncio
import random
from typing import AsyncGenerator, Dict

async def simulate_ambulance_ride() -> AsyncGenerator[Dict, None]:
    minute_counter = 0
    hr_base = 75
    systolic_base = 120
    oxygen_base = 98

    while True:
        minute_counter += 1
        
        hr = hr_base + random.randint(-2, 2)
        systolic = systolic_base + random.randint(-4, 4)
        oxygen = oxygen_base + random.randint(-1, 0)
        
        if 15 < minute_counter <= 30:
            hr_base += random.uniform(1, 3)
            systolic_base -= random.uniform(1, 2.5)
            if random.random() > 0.5:
                oxygen_base -= 1
                
        elif 30 < minute_counter:
            hr_base += random.uniform(2, 5)
            systolic_base -= random.uniform(2, 4)
            oxygen_base -= random.uniform(0.5, 1.5)
            
        hr = max(30, min(hr, 220))
        systolic = max(40, min(systolic, 200))
        oxygen = max(60, min(oxygen, 100))

        vitals = {
            "timestamp": minute_counter,
            "heart_rate": int(hr),
            "blood_pressure": int(systolic),
            "oxygen_saturation": int(oxygen),
            "status": "High Risk" if minute_counter > 30 else ("Medium Risk" if minute_counter > 15 else "Low Risk")
        }
        
        yield vitals
        await asyncio.sleep(1)
