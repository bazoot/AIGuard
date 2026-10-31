import os
import asyncio
import httpx
from colours import printC

class RobloxApiClient:
    def __init__(self):
        # Retrieve roblox API key from env variables
        self.apiKey = os.getenv("ROBLOSECURITY", "") or os.getenv("ROBLOX_API_KEY", "")
        
        if not self.apiKey and os.path.exists("APIkey.txt"):
            try:
                with open("APIkey.txt", "r") as f:
                    self.apiKey = f.read().strip()
                printC("[API Client] : Successfully loaded API key", "brightGreen")
            except Exception as e:
                printC(f"[API Client] : Error reading APIKey.txt: {e}", "brightRed")
                
        self.cookieValue = ""
        if os.path.exists("cookie.txt"):
            try:
                with open("cookie.txt", "r") as f:
                    self.cookieValue = f.read().strip()
            except Exception as e:
                printC(f"[API Client] : Error reading cookie.txt: {e}", "brightRed")
        
        self.cloudBaseUrl = "https://apis.roblox.com/cloud/v2"
        self.thumbnailsBaseUrl = "https://thumbnails.roblox.com/v1"
        self.gamesBaseUrl = "https://games.roblox.com/v1"
        
        # Rate limit tracking: 100 rpm for universes
        self.requestWindowSeconds = 60.0
        self.maxRequestsPerMinute = 98 # 2 request safety buffer
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
        cloudEndpoint = f"{self.cloudBaseUrl}/universes/{universeId}"
        thumbnailsEndpoint = f"{self.thumbnailsBaseUrl}/games/multiget/thumbnails"
        gamesEndpoint = f"{self.gamesBaseUrl}/games"
        votesEndpoint = f"{self.gamesBaseUrl}/games/{universeId}/votes"
        
        browserHeaders = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.roblox.com/",
            "Origin": "https://www.roblox.com",
            "Accept": "application/json"
        }
        
        headers = {
            "x-api-key": self.apiKey,
            "Accept": "application/json"
        }
        
        cookies = {".ROBLOSECURITY": self.cookieValue} if self.cookieValue else {}
        
        retries = 3
        backoffFactor = 2.0
        
        async with httpx.AsyncClient() as client:
            for attempt in range(retries):
                await self._enforceRateLimit()
                try:
                    cloudResponse = await client.get(cloudEndpoint, headers=headers, timeout=10.0)
                    
                    if cloudResponse.status_code == 200:
                        cloudData = cloudResponse.json()
                        
                        rawRootPlace = cloudData.get("rootPlace") or cloudData.get("root_place")
                        placeId = None
                        if isinstance(rawRootPlace, str) and "/" in rawRootPlace:
                            try:
                                placeId = int(rawRootPlace.split("/")[-1])
                            except ValueError:
                                placeId = None
                                
                        # FIXED: Correct key lookups without string literal evaluation bugs
                        title = (
                            cloudData.get("displayName") or 
                            cloudData.get("display_name") or 
                            cloudData.get("name") or 
                            "Unknown Game"
                        )
                        description = cloudData.get("description", "")
                        createdAt = cloudData.get("createTime") or cloudData.get("create_time")
                        updatedAt = cloudData.get("updateTime") or cloudData.get("update_time")
                        
                        thumbnailUrl = ""
                        thumbParams = {
                            "universeIds": universeId,
                            "size": "768x432",
                            "format": "Png",
                            "isCircular": "false"
                        }
                        thumbResponse = await client.get(thumbnailsEndpoint, params=thumbParams, headers=browserHeaders, cookies=cookies, timeout=10.0)
                        if thumbResponse.status_code == 200:
                            thumbJson = thumbResponse.json()
                            thumbDataList = thumbJson.get("data", [])
                            if thumbDataList:
                                thumbnailsList = thumbDataList[0].get("thumbnails", [])
                                if thumbnailsList:
                                    thumbnailUrl = thumbnailsList[0].get("imageUrl", "")
                                    
                        visits = 0
                        likes = 0
                        dislikes = 0
                        
                        # 1. Fetch Likes & Dislikes from Games API (/v1/games?universeIds=)
                        gameParams = {"universeIds": universeId}
                        gamesResponse = await client.get(gamesEndpoint, params=gameParams, headers=browserHeaders, cookies=cookies, timeout=10.0)
                        if gamesResponse.status_code == 200:
                            gamesJson = gamesResponse.json()
                            gamesList = gamesJson.get("data", [])
                            if gamesList:
                                gameInfo = gamesList[0]
                                likes = gameInfo.get("totalUpVotes", 0)
                                dislikes = gameInfo.get("totalDownVotes", 0)

                        # 2. Fetch Visits using placeId via multiget-place-details
                        if placeId:
                            placeDetailsEndpoint = f"{self.gamesBaseUrl}/games/multiget-place-details"
                            placeParams = {"placeIds": placeId}
                            placeResponse = await client.get(placeDetailsEndpoint, params=placeParams, headers=browserHeaders, cookies=cookies, timeout=10.0)
                            if placeResponse.status_code == 200:
                                placeJson = placeResponse.json()
                                if placeJson and isinstance(placeJson, list):
                                    visits = placeJson[0].get("visits", 0)
                        
                        return {
                            "universeId": universeId,
                            "rootPlaceId": placeId,
                            "title": title,
                            "description": description,
                            "thumbnail_url": thumbnailUrl,
                            "likes": likes,
                            "dislikes": dislikes,
                            "visits": visits,
                            "updated_at": updatedAt,
                            "created_at": createdAt
                        }
                    elif cloudResponse.status_code == 404:
                        printC(f"[API Client] : Universe ID {universeId} not found or private", "brightRed")
                        return None
                    elif cloudResponse.status_code == 429:
                        waitDuration = backoffFactor ** (attempt + 1)
                        printC(f"[API Client] : Rate limited (429) on universe {universeId}. Retrying in {waitDuration}s...", "brightYellow")
                    else:
                        printC(f"[API Client] : Error HTTP {cloudResponse.status_code} for universe {universeId}", "brightRed")
                        return None
                except Exception as e:
                    printC(f"[API Client] : Exception occured while fetching universe {universeId}: {e}", "brightRed")
                    await asyncio.sleep(1.0)
            return None