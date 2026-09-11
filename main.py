from fastapi import FastAPI, Query, HTTPException
import httpx

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Weather service is running"}


@app.get("/weather")
async def get_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):

    # -------------------------
    # Weather API
    # -------------------------

    weather_url = "https://api.open-meteo.com/v1/forecast"

    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
    }

    # -------------------------
    # Location API
    # -------------------------

    loc_url = "https://nominatim.openstreetmap.org/reverse"

    loc_params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }

    headers = {
        "User-Agent": "weather-service"
    }

    # -------------------------
    # Make async requests
    # -------------------------

    async with httpx.AsyncClient() as client:

        # Weather request
        try:
            response = await client.get(
                weather_url,
                params=weather_params,
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Weather API request timed out"
            )

        except httpx.HTTPError:
            raise HTTPException(
                status_code=502,
                detail="Weather API is unavailable"
            )

        # Location request
        try:
            loc_response = await client.get(
                loc_url,
                params=loc_params,
                headers=headers,
                timeout=20
            )

            loc_response.raise_for_status()

            loc_data = loc_response.json()

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Location API request timed out"
            )

        except httpx.HTTPError:
            raise HTTPException(
                status_code=502,
                detail="Location API is unavailable"
            )

    # -------------------------
    # Extract location
    # -------------------------

    address = loc_data.get("address", {})

    place = (
        address.get("city")
        or address.get("town")
        or address.get("municipality")
        or address.get("village")
        or address.get("suburb")
        or address.get("city_district")
    )

    country = address.get("country")

    # -------------------------
    # Return response
    # -------------------------

    return {
        "location": {
            "place": place,
            "country": country
        },
        "weather": {
            "temperature": data["current"]["temperature_2m"],
            "humidity": data["current"]["relative_humidity_2m"]
        }
    }