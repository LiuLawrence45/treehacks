from threading import Lock

# Initialize a lock and a flag
execution_lock = Lock()
has_executed = False