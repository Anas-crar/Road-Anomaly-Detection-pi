import time
import sys
from core.system import AnomalyDetectorSystem
from utils.logger import log_event

def main():
    system = AnomalyDetectorSystem()
    
    try:
        system.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        log_event("⚠️ User interrupted")
    finally:
        system.stop()

if __name__ == "__main__":
    main()
