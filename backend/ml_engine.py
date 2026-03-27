import numpy as np
from collections import deque

class AnomalyDetector:
    def __init__(self, window_size=30, threshold=3.0):
        self.window_size = window_size
        self.threshold = threshold
        self.history = deque(maxlen=window_size)
    
    def process_new_metric(self, value: float) -> bool:
        """
        Returns True if the new value is an anomaly.
        Uses a simple Z-score sliding window method.
        """
        if len(self.history) < self.window_size:
            self.history.append(value)
            return False
            
        mean = np.mean(self.history)
        std_dev = np.std(self.history)
        
        if std_dev == 0: # Avoid division by zero
            z_score = 0
        else:
            z_score = abs(value - mean) / std_dev
            
        self.history.append(value)
        return z_score > self.threshold
