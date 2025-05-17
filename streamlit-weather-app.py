import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(
    page_title="Weather by Zip Code",
    page_icon="🌤️",
    layout="centered"
)

# App title and description
st.title("📍 Weather by Zip Code")
st.markdown("Enter a US zip code to get the current weather conditions.")

# Function to get weather data
def get_weather(zip_code, api_key):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "zip": f"{zip_code},us",
        "appid": api_key,
        "units": "imperial"  # For Fahrenheit (use "metric" for Celsius)
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None

# Sidebar for API key input
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenWeatherMap API Key", type="password", 
                           help="Get your free API key from openweathermap.org")
    
    # Unit selection
    unit_system = st.radio(
        "Temperature Unit",
        options=["Fahrenheit (°F)", "Celsius (°C)"],
        index=0
    )
    
    # Information about the app
    st.markdown("---")
    st.markdown("### About")
    st.info("""
    This app uses the OpenWeatherMap API to fetch real-time weather data.
    You'll need a free API key from [openweathermap.org](https://openweathermap.org) to use this app.
    """)

# Main content
zip_code = st.text_input("Enter ZIP Code:", max_chars=5)

# Check if we should use metric units
use_metric = "Celsius" in unit_system

# Only proceed if both zip code and API key are provided
if zip_code and api_key:
    if len(zip_code) != 5 or not zip_code.isdigit():
        st.warning("Please enter a valid 5-digit ZIP code.")
    else:
        # Show a spinner while fetching data
        with st.spinner("Fetching weather data..."):
            # Update API parameters based on unit selection
            base_url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "zip": f"{zip_code},us",
                "appid": api_key,
                "units": "metric" if use_metric else "imperial"
            }
            
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                weather_data = response.json()
                
                # Extract required information
                city_name = weather_data["name"]
                temp = weather_data["main"]["temp"]
                feels_like = weather_data["main"]["feels_like"]
                humidity = weather_data["main"]["humidity"]
                pressure = weather_data["main"]["pressure"]
                wind_speed = weather_data["wind"]["speed"]
                description = weather_data["weather"][0]["description"]
                icon_code = weather_data["weather"][0]["icon"]
                
                # Convert timestamp to readable date/time
                sunrise_time = datetime.fromtimestamp(weather_data["sys"]["sunrise"]).strftime("%I:%M %p")
                sunset_time = datetime.fromtimestamp(weather_data["sys"]["sunset"]).strftime("%I:%M %p")
                
                # Get weather icon URL
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                
                # Display location and current conditions
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(icon_url, width=100)
                
                with col2:
                    st.header(f"{city_name}")
                    st.subheader(f"{description.capitalize()}")
                    temp_unit = "°C" if use_metric else "°F"
                    speed_unit = "m/s" if use_metric else "mph"
                    st.markdown(f"### {temp:.1f} {temp_unit}")
                    st.write(f"Feels like: {feels_like:.1f} {temp_unit}")
                
                # Create three columns for additional information
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Humidity", f"{humidity}%")
                
                with col2:
                    st.metric("Wind Speed", f"{wind_speed} {speed_unit}")
                
                with col3:
                    st.metric("Pressure", f"{pressure} hPa")
                
                # Sunrise and sunset times
                st.markdown("---")
                sun_col1, sun_col2 = st.columns(2)
                
                with sun_col1:
                    st.write("🌅 Sunrise: " + sunrise_time)
                
                with sun_col2:
                    st.write("🌇 Sunset: " + sunset_time)
                
                # Additional forecast data if available
                if "rain" in weather_data:
                    rain_1h = weather_data["rain"].get("1h", 0)
                    st.write(f"Rain (last hour): {rain_1h} mm")
                
                # Display some historical data (note: this requires a different API endpoint in a real app)
                st.markdown("---")
                st.subheader("24-Hour Forecast")
                st.info("Note: For a full forecast, you would need to use the OpenWeatherMap One Call API.")
                
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching weather data: {e}")
            except KeyError as e:
                st.error(f"Could not parse weather data: {e}")
                if "message" in weather_data:
                    st.error(f"API message: {weather_data['message']}")
else:
    # Show instructions when the app first loads
    if not api_key:
        st.info("👈 Please enter your OpenWeatherMap API key in the sidebar.")
    if not zip_code:
        st.info("Please enter a ZIP code above to get started.")

# Footer
st.markdown("---")
st.caption("Data provided by OpenWeatherMap")
