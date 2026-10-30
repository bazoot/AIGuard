import asyncio
import httpx
import os
from colours import printC
from database import checkIfUniverseExists

class JobDispatcher:
    def __init__(self, targetBatchSize: int = 5):
        self.targetBatchSize = targetBatchSize
        self.baseUrl = "https://games.roblox.com/v1/games/list"
        self.nextPaginationKey = ""
        self.dispatchLock = asyncio.Lock()
        self.scannedCache = set()
        
        self.cookieValue = ""
        if os.path.exists("cookie.txt"):
            try:
                with open("cookie.txt", "r") as f:
                    self.cookieValue = f.read().strip()
                printC("[Job Dispatcher] : Successfully loaded security cookies", "cyan")
            except Exception as e:
                printC("[Job Dispatcher] : Error reading cookie.txt: {e}", "brightRed")
        else:
            printC("[Job Dispatcher] : Warning: cookie.txt not found. Web endpoints may return 403 Unauthorised.", "brightYellow")
        
    async def fetchPopularGameIds(self) -> list[int]:
        params = {
            "sortToken": "default",
            "maxRows": 50,
            "isTruncatedResultsEnabled": "true"
        }
        
        if self.nextPaginationKey:
            params["paginationKey"] = self.nextPaginationKey
            
        cookies = {".ROBLOSECURITY": self.cookieValue} if self.cookieValue else {}
        discoveredIds = []
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.baseUrl, params=params, cookies=cookies, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    
                    self.nextPaginationKey = data.get("nextPaginationKey", "")
                    
                    gamesList = data.get("games", [])
                    items = gamesList.get("data", []) if isinstance(gamesList, dict) else gamesList
                    
                    for game in items:
                        universeId = game.get("universeId")
                        if universeId and universeId not in self.scannedCache:
                            discoveredIds.append(universeId)
                else:
                    printC(f"[Job Dispatcher] : Failed to fetch popular games list. HTTP {response.status_code}", "brightRed")
            except Exception as e:
                printC(f"[Job Dispatcher] : Error fetching popular games list: {e}", "cyan")
                
        return discoveredIds
    
    async def requestBatchofIds(self) -> list[int]:
        async with self.dispatchLock:
            printC("[Job Dispatcher] : Compiling new ID batch for worker...", "cyan")
            tempIdStack = []
            
            while len(tempIdStack) < self.targetBatchSize:
                rawDiscoveredIds = await self.fetchPopularGameIds()
                
                if not rawDiscoveredIds:
                    printC("[Job Dispatcher] : Reached end of popularity catalog")
                    break
                
                for universeId in rawDiscoveredIds:
                    if len(tempIdStack) >= self.targetBatchSize:
                        break
                
                    self.scannedCache.add(universeId)
                
                    exists = await checkIfUniverseExists(universeId)
                    if exists:
                        continue
                    else:
                        tempIdStack.append(universeId)
                        
            printC(f"[Job Dispatcher] : Dispatched verified discovery batch of {len(tempIdStack)} Ids.", "cyan")
            return tempIdStack
            