import asyncio
import sys
import httpx
from database import checkDatabaseExists, createDatabase, dbFile, insertGameIntoDatabase
from dispatcher import JobDispatcher
from colours import printC

async def checkInternetConnection() -> int:
    #check reachability to internet and roblox apis
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://apis.roblox.com", timeout=5.0)
            return response.status_code
        except Exception:
            return -1 # No Connection code

async def workerNode(workerId: int, dispatcher: JobDispatcher):
    localQueue = []
    
    while True:
        # check if local queue is empty
        if not localQueue:
            printC(f"[Worker {workerId}] : Local ID queue empty. Requesting ID queue from dispatcher", "brightMagenta")
            localQueue = await dispatcher.requestBatchofIds()
            
            if not localQueue:
                printC(f"[Worker {workerId}] : No more IDs available. Worker terminating", "brightMagenta")
                break
            
        # get next ID
        universeId = localQueue.pop(0)
        printC(f"[Worker {workerId}] : Processing Universe ID {universeId}", "brightMagenta")
        
        # Game validation (exists? and public?)
        # this is a mockup
        gameValid = True
        if not gameValid:
            printC(f"[Worker {workerId}] : ID {universeId} is invalid or private. Skipped", "brightMagenta")
            continue
        
        # Request game details from API
        try:
            # Placeholder for Cloud v2/games API request
            await asyncio.sleep(0.3)
            
            # Write to database
            mockTitle = f"Mock title {universeId}"
            mockDescription = f"Mock Description"
            await insertGameIntoDatabase(universeId, mockTitle, mockDescription)
            printC(f"[Worker {workerId}] : Successfully stored details for Universe ID {universeId}", "brightMagenta")
        except Exception as e:
            printC(f"[Worker {workerId}] : Error processing Universe ID {universeId}: {e}", "brightMagenta")

async def main():
    print("[System] : Starting...")
    
    # DB existance check
    if not await checkDatabaseExists():
        print("[System] : Database not found. Creating...")
        try:
            await createDatabase()
            printC("[System] : Database initialised successfully", "brightGreen")
        except Exception as e:
            printC(f"[System] : Fatal error : DDL failed. Exception {e}", "brightRed")
            print("[System] : Exiting...", "brightRed")
            sys.exit(1)
    else:
        print("[System] : Main DB found")
    
    # Internet Connection Check
    print("[System] : Verifying internet connection...")
    statusCode = await checkInternetConnection()
    if statusCode > 500:
        printC(f"[System] : Fatal Exception : No internet connection or unreachable API. Status {statusCode}", "brightRed")
        printC("[System] : Exiting...", "brightRed")
        sys.exit(1)
    printC(f"[System] : Connection verified with status {statusCode}", "brightGreen")
    
    # Initialise job dispatcher
    jobDispatcher = JobDispatcher(targetBatchSize=3)
    
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
    printC("[System] : Scan cycle completed successfully", "brightGreen", "bold", "underline")
    
if __name__ == "__main__":
    asyncio.run(main())