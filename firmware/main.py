import machine
from time import sleep

try:
    from app import main
    main()
except Exception:
    sleep(30)
    machine.reset()
