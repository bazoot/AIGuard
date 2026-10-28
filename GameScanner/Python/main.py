import asyncio
import sys
import httpx
from database import checkDatabaseExists, createDatabase, dbFile
from dispatcher import jobDispatcher

async def checkInternetConnection() -> int:
    #check reachability to internet and roblox apis
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://apis.roblox.com", timeout=5.0)
            return response.status_code
        except Exception:
            return -1 # No Connection code

async def workerNode(workerId: int, dispatcher: jobDispatcher):
    localQueue = []
    
    while True:
        # check if local queue is empty
        if not localQueue:
            print(f"[Worker {workerId}] : Local ID queue empty. Requesting ID queue from dispatcher")
            localQueue = await dispatcher.requestBatchofIds()
            
            if not localQueue:
                print(f"[Worker {workerId}] : No more IDs available. Worker terminating")
                break
            
        # get next ID
        universeId = localQueue.pop(0)
        print(f"[Worker {workerId}] : Processing Universe ID {universeId}")
        
        # Game validation (exists? and public?)
        # this is a mockup
        gameValid = True
        if not gameValid:
            print(f"[Worker {workerId}] : ID {universeId} is invalid or private. Skipped")
            continue
        
        # Request game details from API
        try:
            # Placeholder for Cloud v2/games API request
            await asyncio.sleep(0.3)
            
            # Store details in main db
            print(f"[Worker {workerId}] : Successfully stored details for Universe ID {universeId}")
        except Exception as e:
            print(f"[Worker {workerId}] : Error processing Universe ID {universeId}: {e}")

async def main():
    print("[System] : Starting...")
    
    # DB existance check
    if not await checkDatabaseExists():
        print("[System] : Database not found. Creating...")
        try:
            await createDatabase()
            print("[System] : Database initialised successfully")
        except Exception as e:
            print(f"[System] : Fatal error : DDL failed. Exception {e}")
            print("[System] : Exiting...")
            sys.exit(1)
    else:
        print("[System] : Main DB found")
    
    # Internet Connection Check
    print("[System] : Verifying internet connection...")
    statusCode = await checkInternetConnection()
    if statusCode != 200:
        print(f"[System] : Fatal Exception : No internet connection or unreachable API. Status {statusCode}")
        print("[System] : Exiting...")
        sys.exit(1)
    print(f"[System] : Connection verified with status {statusCode}")
    
    # Initialise job dispatcher
    jobDispatcher = jobDispatcher(targetBatchSize=3)
    
    # Spawn parallel workers
    numberOfWorkers = 2
    print(f"[System] : Spawning {numberOfWorkers} parallel worker tasks...")
    
    workerTasks = []
    for i in range(numberOfWorkers):
        workerId = i + 1
        task = asyncio.create_task(workerNode(workerId, jobDispatcher))
        workerTasks.append(task)
    
    # Run workers concurrently until complete
    await asyncio.gather(*workerTasks)
    print("[System] : Scan cycle completed successfully")
    
if __name__ == "__main__":
    asyncio.run(main())