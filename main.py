from fastapi import FastAPI ,Query
import requests

app=FastAPI()

@app.get("/")
def home():
    return {"message":"Weather service is running"}

@app.get("/weather")
def get_weather(lat:float= Query(..., ge=-90, le=90),lon:float= Query(..., ge=-180, le=180)):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
    }
    response = requests.get(url, params=params)
    data=response.json()

    loc_url="https://nominatim.openstreetmap.org/reverse"
    loc_params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    headers = {
        "User-Agent": "weather-service"
    }

    loc_response=requests.get(loc_url,params=loc_params,headers=headers)
    loc_data=loc_response.json()
    address = loc_data.get("address", {})


    return{
        "location": {"city":address.get("city")
                     or address.get("town")
                     or address.get("village")
                     or address.get("municipality")
                     ,"country":address.get("country")},
        "weather": {
            "temperature": data["current"]["temperature_2m"],
            "humidity": data["current"]["relative_humidity_2m"]
        }
    }