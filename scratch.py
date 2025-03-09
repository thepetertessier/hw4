import multiprocessing
import time

def main_logic():
    # Simulating a long-running process
    time.sleep(60)  # This will exceed the 50-second limit
    print("Main logic finished")

def run_with_timeout():
    process = multiprocessing.Process(target=main_logic)
    process.start()
    process.join(timeout=2)  # Wait up to 50 seconds
    
    if process.is_alive():
        process.terminate()
        process.join()
        print("took too long")
    else:
        print("Main logic completed within time")

if __name__ == "__main__":
    run_with_timeout()
