import asyncio
import httpx
import os
from colours import printC
from database import checkIfUniverseExists
from datetime import datetime

class JobDispatcher:
    def __init__(self, targetBatchSize: int = 100):
        self.targetBatchSize = targetBatchSize
        self.baseUrl = "https://games.roblox.com/v1/games/list"
        self.currentUniversePointer = 6500000000
        self.historyFile = "scan_history.txt"
        self.dispatchLock = asyncio.Lock()
        self._logScanSession()
        
    def _logScanSession(self):
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        logEntry = f"{timestamp} | {self.currentUniversePointer}"
        try:
            with open(self.historyFile, "a" if os.path.exists(self.historyFile) else "w") as f:
                f.write(logEntry)
            printC(f"[Job Dispatcher] Recorded scan session to {self.historyFile}", "brightGreen")
        except Exception as e:
            printC(f"[Job Dispatcher] : Failed to record scan session: {e}", "brightRed")
            
    async def fetchDiscoveryGameIds(self) -> list[int]:
        rawIds = []
        for _ in range(self.targetBatchSize * 100):
            if self.currentUniversePointer > 0:
                rawIds.append(self.currentUniversePointer)
                self.currentUniversePointer -= 1
        return rawIds

    async def requestBatchofIds(self) -> list[int]:
        async with self.dispatchLock:
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
                        
            printC(f"[Job Dispatcher] : Dispatched verified discovery batch of {len(tempIdStack)} Ids.", "cyan")
            return tempIdStack
            