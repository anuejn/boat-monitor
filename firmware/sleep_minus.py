from time import time_ns, sleep_ms

last = None

def time():
    return time_ns() / 1e9

def sleep(seconds):
    sleep_ms(int(seconds * 1000))

def sleep_minus(seconds):
    global last
    if last is None:
        last = time()

    to_wait = last - time() + seconds
    last = time()
    if to_wait < 0:
        print(f"Warning: something took to long! we are {-(to_wait):.2f}s behind shedule")
    else:
        print(f"Sleeping for {(to_wait):.2f} seconds")
        sleep(to_wait)
