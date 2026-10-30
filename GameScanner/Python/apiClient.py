import os
import asyncio
import httpx
from colours import printC

class RobloxApiClient:
    def __init__(self):
        # Retrieve roblox API key from env variables
        self.apiKey = os.getenv("ROBLOX_API_KEY", "")
        
        if not self.apiKey and os.path.exists("APIkey.txt"):
            try:
                with open("APIkey.txt", "r") as f:
                    self.apiKey = f.read().strip()
                printC("[API Client] : Successfully loaded API key", "brightGreen")
            except Exception as e:
                printC(f"[API Client] : Error reading APIKey.txt: {e}", "brightRed")
        self.baseUrl = "https://apis.roblox.com"
        # Rate limit tracking: 100 rpm for universes
        self.requestWindowSeconds = 60.0
        self.maxRequestsPerMinute = 95 # 5 request safety buffer
        self.requestTimestamps = []
        
    async def _enforceRateLimit(self):
        # Token bucket to prevent 429 too many requests
        currentTime = float(asyncio.get_event_loop().time())
        # Filter timestamps within last 60 seconds
        self.requestTimestamps = [
            float(t) for t in self.requestTimestamps 
            if isinstance(t, (int, float)) and (currentTime - float(t) < self.requestWindowSeconds)]
        
        if len(self.requestTimestamps) >= self.maxRequestsPerMinute:
            oldestTimestamp = float(self.requestTimestamps[0])
            sleepTime = self.requestWindowSeconds - (currentTime - oldestTimestamp) + 0.5
            if sleepTime > 0:
                printC(f"[API Client] : Rate limit approaching - throttling for {sleepTime:.2f} seconds...", "brightBlue")
                await asyncio.sleep(sleepTime)
            currentTime = float(asyncio.get_event_loop().time())
            
        self.requestTimestamps.append(asyncio.get_event_loop().time())
        
    async def fetchUniverseDetails(self, universeId: int) -> dict | None:
        endpoint = f"{self.baseUrl}/cloud/v2/universes/{universeId}"
        headers = {
            "x-api-key": self.apiKey,
            "Accept": "application/json"
        }
        
        retries = 3
        backoffFactor = 2.0
        
        async with httpx.AsyncClient() as client:
            for attempt in range(retries):
                await self._enforceRateLimit()
                try:
                    response = await client.get(endpoint, headers=headers, timeout=10.0)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Normalise or extract necessary fields
                        return {
                            "universeId": universeId,
                            "rootPlaceId": data.get("rootPlaceId"),
                            "title": data.get("name"),
                            "description": data.get("description"),
                            "thumbnail_url": data.get("thumbnail_url"),
                            "likes": data.get("likes"),
                            "dislikes": data.get("dislikes"),
                            "visits": data.get("visits"),
                            "updated_at": data.get("updateTime"),
                            "created_at": data.get("createTime")
                        }
                    elif response.status_code == 404:
                        printC(f"[API Client] : Universe ID {universeId} not found or private", "brightRed")
                        return None
                    elif response.status_code == 429:
                        waitDuration = backoffFactor ** (attempt + 1)
                        printC(f"[API Client] : Rate limited (429) on universe {universeId}. Retrying in {waitDuration}s...", "brightYellow")
                    else:
                        printC(f"[API Client] : Error HTTP {response.status_code} for universe {universeId}", "brightRed")
                        return None
                except Exception as e:
                    printC(f"[API Client] : Exception occured while fetching universe {universeId}: {e}", "brightRed")
                    await asyncio.sleep(1.0)
            return None