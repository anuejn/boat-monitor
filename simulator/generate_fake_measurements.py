import sys
import time
import math

for i in range(int(sys.argv[1])):
    print(f"temperature temperature={math.sin(i)} {int(time.time() + i * 10)}")
