from fastapi import FastAPI, Query, HTTPException
import httpx
import asyncio

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Weather service is running"}


async def get_weather_data(client, lat, lon):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
    }

    try:
        response = await client.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

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


async def get_location_data(client, lat, lon):

    loc_url = "https://nominatim.openstreetmap.org/reverse"

    loc_params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }

    headers = {
        "User-Agent": "weather-service"
    }

    try:
        response = await client.get(
            loc_url,
            params=loc_params,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

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


@app.get("/weather")
async def get_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):

    async with httpx.AsyncClient() as client:

        weather_task = get_weather_data(
            client,
            lat,
            lon
        )

        location_task = get_location_data(
            client,
            lat,
            lon
        )

        data, loc_data = await asyncio.gather(
            weather_task,
            location_task
        )

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