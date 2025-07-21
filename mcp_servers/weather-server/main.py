import os
import httpx
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Weather MCP Server", version="1.0.0")

class ToolRequest(BaseModel):
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    content: str
    success: bool = True

# Mock weather data for demonstration
MOCK_WEATHER_DATA = {
    "new york": {"temp": 22, "description": "partly cloudy", "humidity": 65},
    "london": {"temp": 15, "description": "rainy", "humidity": 80},
    "tokyo": {"temp": 28, "description": "sunny", "humidity": 55},
    "paris": {"temp": 18, "description": "overcast", "humidity": 70},
    "sydney": {"temp": 25, "description": "sunny", "humidity": 60},
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "weather-mcp"}

@app.get("/tools")
async def get_tools():
    """Get available tools"""
    return {
        "tools": [
            {
                "name": "get_weather",
                "description": "Get current weather information for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city name to get weather for"
                        }
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "get_forecast",
                "description": "Get weather forecast for a city",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city name to get forecast for"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days for forecast (1-7)",
                            "default": 3
                        }
                    },
                    "required": ["city"]
                }
            }
        ]
    }

@app.get("/resources")
async def get_resources():
    """Get available resources"""
    return {
        "resources": [
            {
                "uri": "weather://cities",
                "name": "Available Cities",
                "description": "List of cities with weather data"
            }
        ]
    }

@app.post("/tools/get_weather")
async def get_weather(request: ToolRequest) -> ToolResponse:
    """Get current weather for a city"""
    try:
        city = request.arguments.get("city", "").lower().strip()
        
        if not city:
            raise HTTPException(status_code=400, detail="City parameter is required")
        
        # Use mock data for demonstration
        weather_data = MOCK_WEATHER_DATA.get(city)
        
        if not weather_data:
            # Return a generic response for unknown cities
            weather_data = {"temp": 20, "description": "partly cloudy", "humidity": 60}
            logger.info(f"Using mock data for unknown city: {city}")
        
        result = f"Weather in {city.title()}: {weather_data['description']}, {weather_data['temp']}°C, humidity {weather_data['humidity']}%"
        
        logger.info(f"Weather request for {city}: {result}")
        return ToolResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting weather: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/get_forecast")
async def get_forecast(request: ToolRequest) -> ToolResponse:
    """Get weather forecast for a city"""
    try:
        city = request.arguments.get("city", "").lower().strip()
        days = request.arguments.get("days", 3)
        
        if not city:
            raise HTTPException(status_code=400, detail="City parameter is required")
        
        if days < 1 or days > 7:
            days = 3
        
        # Generate mock forecast data
        base_weather = MOCK_WEATHER_DATA.get(city, {"temp": 20, "description": "partly cloudy", "humidity": 60})
        
        forecast_lines = [f"Weather forecast for {city.title()} ({days} days):"]
        
        for day in range(1, days + 1):
            # Vary temperature slightly for each day
            temp_variation = (day - 1) * 2 - 2  # -2, 0, 2, 4...
            temp = base_weather["temp"] + temp_variation
            forecast_lines.append(f"Day {day}: {base_weather['description']}, {temp}°C")
        
        result = "\n".join(forecast_lines)
        
        logger.info(f"Forecast request for {city} ({days} days)")
        return ToolResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resources/weather://cities")
async def get_cities_resource():
    """Get list of available cities"""
    cities = list(MOCK_WEATHER_DATA.keys())
    return {
        "content": f"Available cities: {', '.join(city.title() for city in cities)}",
        "mimeType": "text/plain"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
