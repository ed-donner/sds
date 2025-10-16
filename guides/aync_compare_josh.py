import time
import asyncio

# Blocking version
def blocking_loop():
    start = time.time()
    for i in range(3):
        time.sleep(1)
        print(f"Blocking iteration {i+1} done")
    end = time.time()
    print(f"Blocking total time: {end - start:.2f} seconds\n")

# Async version
async def non_blocking_task(i):
    await asyncio.sleep(1)
    print(f"Async iteration {i+1} done")

async def non_blocking_loop():
    start = time.time()
    tasks = [non_blocking_task(i) for i in range(3)]
    await asyncio.gather(*tasks)
    end = time.time()
    print(f"Async total time: {end - start:.2f} seconds\n")

if __name__ == "__main__":
    print("Running blocking version...")
    blocking_loop()

    print("Running async version...")
    asyncio.run(non_blocking_loop())
