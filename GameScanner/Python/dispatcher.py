import asyncio
import aiosqlite
from colours import printC
from database import checkIfUniverseExists

class JobDispatcher:
    def __init__(self, targetBatchSize: int = 3):
        self.targetBatchSize = targetBatchSize
        self.currentIdPointer = 101
        self.maxIdLimit = 120
        self.dispatchLock = asyncio.Lock()
        
    async def fetchDiscoveryGameIds(self) -> list[int]:
        #In prod, call roblox discovery apis here
        #this returns mock IDs atm
        rawIds = []
        for _ in range(5):
            if self.currentIdPointer <= self.maxIdLimit:
                rawIds.append(self.currentIdPointer)
                self.currentIdPointer += 1
        return rawIds
    
    async def requestBatchofIds(self) -> list[int]:
        async with self.dispatchLock:
            print("[Job Dispatcher] : Received ID queue request. Processing batch...")
            tempIdStack = []
            
            # Actually call the discovery method
            rawDiscoveredIds = await self.fetchDiscoveryGameIds()

            for universeId in rawDiscoveredIds:
                if len(tempIdStack) >= self.targetBatchSize:
                    break
                
                # Check if already in main DB (Deduplication)
                exists = await checkIfUniverseExists(universeId)
                if exists:
                    print(f"[Job Dispatcher] : ID {universeId} already exists in DB. Skipping.")
                    continue
                else:
                    tempIdStack.append(universeId)

            print(f"[Job Dispatcher] Stack dispatched ({len(tempIdStack)} IDs).")
            return tempIdStack