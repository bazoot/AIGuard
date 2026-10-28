import asyncio
import aiosqlite
from colours import printC
from database import checkIfUniverseExists

class JobDispatcher:
    def __init__(self, targetBatchSize: int = 3):
        self.targetBatchSize = targetBatchSize
        self.currentIdPointer = 1000000
        
    async def fetchDiscoveryGameIds(self) -> list[int]:
        batchIds = []
        for _ in range(self.targetBatchSize * 3):
            batchIds.append(self.currentIdPointer)
            self.currentIdPointer += 1
        return batchIds
    
    async def requestBatchofIds(self) -> list[int]:
        printC("[Job Dispatcher] : Compiling new ID batch for worker...", "cyan")
        tempIdStack = []
        rawDiscoveredIds = await self.fetchDiscoveryGameIds()
        for universeId in rawDiscoveredIds:
            if len(tempIdStack) >= self.targetBatchSize:
                break
            
            exists = await checkIfUniverseExists(universeId)
            if exists:
                continue
            else:
                tempIdStack.append(universeId)
            
        printC(f"[Job Dispatcher] : Dispatched batch of {len(tempIdStack)} IDs.", "cyan")
        return tempIdStack