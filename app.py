import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Function to get coordinates (latitude, longitude) of a city using Open-Meteo API
def get_coordinates(city_name):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
    response = requests.get(geo_url)
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            location = data["results"][0]
            return location["latitude"], location["longitude"], location["name"], location["country"]
    return None

# Function to get current weather of a city using Open-Meteo API
def get_weather(lat, lon):
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    response = requests.get(weather_url)
    if response.status_code == 200:
        return response.json().get("current_weather", {})
    return None

# Function to get air quality data for a city using Open-Meteo API
def get_air_quality(lat, lon):
    air_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone"
    response = requests.get(air_url)
    if response.status_code == 200:
        data = response.json()
        if "hourly" in data:
            index = 0  # Get latest hour
            air = {
                "pm10": data["hourly"]["pm10"][index],
                "pm2_5": data["hourly"]["pm2_5"][index],
                "co": data["hourly"]["carbon_monoxide"][index],
                "no2": data["hourly"]["nitrogen_dioxide"][index],
                "so2": data["hourly"]["sulphur_dioxide"][index],
                "o3": data["hourly"]["ozone"][index],
                "time": data["hourly"]["time"][index]
            }
            return air
    return None

# Function to calculate AQI based on PM2.5 concentration
def calculate_aqi(pm2_5):
    if pm2_5 <= 50:
        return "Good"
    elif 51 <= pm2_5 <= 100:
        return "Moderate"
    elif 101 <= pm2_5 <= 150:
        return "Unhealthy for sensitive groups"
    elif 151 <= pm2_5 <= 200:
        return "Unhealthy"
    elif 201 <= pm2_5 <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

# Function to provide industry-specific suggestions based on AQI level
def industry_suggestion(aqi_level):
    suggestions = {
        "Good": "Keep maintaining low emissions. No immediate actions required.",
        "Moderate": "Monitor air quality closely. Maintain good operational practices.",
        "Unhealthy for sensitive groups": "Improve air filtration systems and reduce emissions during peak hours.",
        "Unhealthy": "Consider reducing emissions, improve air filtration, and consult with environmental regulators.",
        "Very Unhealthy": "Major operational changes are required to reduce emissions. Consider shutting down operations in high pollution zones.",
        "Hazardous": "Immediate action required! Shut down operations if possible, and provide protective gear to workers. Consult with regulators."
    }
    return suggestions.get(aqi_level, "No suggestions available")

# Home route to handle the city input and fetch the relevant data
@app.route("/", methods=["GET", "POST"])
def index():
    weather_info = None
    air_info = None
    location_info = None
    aqi_info = None
    industry_advice = None  # To store industry-specific suggestion
    
    if request.method == "POST":
        city_name = request.form["city_name"]
        result = get_coordinates(city_name)

        if result:
            lat, lon, city_name, country = result
            location_info = f"{city_name}, {country} (Lat: {lat}, Lon: {lon})"

            # Get weather data for the city
            weather = get_weather(lat, lon)
            if weather:
                weather_info = {
                    "temperature": weather.get("temperature"),
                    "windspeed": weather.get("windspeed"),
                    "time": weather.get("time"),
                }

            # Get air quality data for the city
            air = get_air_quality(lat, lon)
            if air:
                air_info = {
                    "pm10": air.get("pm10"),
                    "pm2_5": air.get("pm2_5"),
                    "co": air.get("co"),
                    "no2": air.get("no2"),
                    "so2": air.get("so2"),
                    "o3": air.get("o3"),
                    "time": air.get("time"),
                }

                # Calculate AQI based on PM2.5 value
                pm2_5_value = air.get("pm2_5")
                if pm2_5_value is not None:
                    aqi_info = calculate_aqi(pm2_5_value)
                    # Provide industry-specific suggestions based on AQI
                    industry_advice = industry_suggestion(aqi_info)

    return render_template("index.html", location_info=location_info, weather_info=weather_info, air_info=air_info, aqi_info=aqi_info, industry_advice=industry_advice)

if __name__ == "__main__":
    app.run(debug=True)