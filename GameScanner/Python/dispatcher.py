import aiosqlite
import httpx
from database import checkIfUniverseExists
class jobDispatcher:
    def __init__(self, targetBatchSize: int = 5):
        self.targetBatchSize = targetBatchSize
        
    async def fetchDiscoveryGameIds(self) -> list[int]:
        #In prod, call roblox discovery apis here
        #this returns mock IDs atm
        return [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    
    async def requestBatchofIds(self) -> list[int]:
        print("[Job Dispatcher] : Recieved ID queue request, Processing batch")
        tempIdStack = []
        rawDiscoveredIds = await self.fetchDiscoveryGameIds()
        
        for universeId in rawDiscoveredIds:
            #Check if stack full
            if len(tempIdStack) >= self.targetBatchSize:
                break
            
            #Check if already in main db
            exists = await checkIfUniverseExists(universeId)
            if exists:
                continue
            else:
                tempIdStack.append(universeId)
                
        print(f"[Job Dispatcher] : Stack Full ({len(tempIdStack)}) IDs. Queue dispatched to worker")
        return tempIdStack