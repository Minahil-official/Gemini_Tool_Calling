from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access keys
weather_api_key = os.getenv("weather_api_key")
google_key = os.getenv("GOOGLE_API_KEY")
News_key = os.getenv("News_api_key")

from langchain_core.tools import tool
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
import streamlit as st


@tool

def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.

    Parameters:
    - expression (str): The mathematical expression to evaluate.

    Returns:
    - str: The result of the evaluation or an error message.
    """
    import math

    # Define a safe dictionary of allowed methods and constants
    allowed_names = {name: getattr(math, name) for name in dir(math) if not name.startswith("__")}
    allowed_names.update({"abs": abs, "round": round})

    try:
        # Use eval with restricted globals for safety
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: Invalid expression. Details: {e}"
    
@tool
# Function to fetch the latest news
def fetch_latest_news(query: str = "latest", language: str = "en", page_size: int = 5):
    """
    Fetches the latest news articles based on a query.

    Parameters:
    - query (str): The keyword for the news search (default is 'latest').
    - language (str): Language for the news (default is 'en').
    - page_size (int): Number of news articles to fetch (default is 5).

    Returns:
    - list: A list of dictionaries with news headlines, descriptions, and URLs.
    """
    base_url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "pageSize": page_size,
        "apiKey": News_key,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        articles = response.json().get("articles", [])

        news = []
        for article in articles:
            news.append({
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
            })

        return news
    except Exception as e:
        return {"error": str(e)}


@tool
# Function to fetch weather
def fetch_weather(city: str) -> str:
    """
    Fetches the current weather for a given city.

    Parameters:
    - city (str): Name of the city to fetch weather for.

    Returns:
    - str: Weather details or error message.
    """
    # Replace with your OpenWeatherMap API key
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "q": city,
        "appid": weather_api_key ,
        "units": "metric"  # Use "imperial" for Fahrenheit
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        
        # Check if the API returned an error
        if data.get("cod") != 200:
            return f"Error: {data.get('message', 'Unknown error occurred.')}"
        
        # Extract weather details
        weather = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        city_name = data["name"]
        
        return (
            f"Weather in {city_name}:\n"
            f"- Description: {weather}\n"
            f"- Temperature: {temperature}°C\n"
            f"- Humidity: {humidity}%"
        )
    except requests.exceptions.RequestException as e:
        return f"Error: Unable to fetch weather data. Details: {e}"
    except KeyError:
        return "Error: Unable to parse weather data. Please check the city name."
    


tools = [calculator, fetch_latest_news, fetch_weather]

llm = ChatGoogleGenerativeAI(model = "gemini-2.0-flash-exp" , api_key=google_key)


# Define the tools list using the Tool objects
# and the calculator function decorated with @tool
tools = [calculator, fetch_latest_news, fetch_weather]

agent = initialize_agent(tools, llm , agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION )


# Streamlit App UI
st.title("Tool Calling App")

# Adding a description with CSS for a blurred effect
st.markdown(
    """
    <style>
    .app-description {
        color: #6c757d; /* Subtle gray color */
        font-size: 18px;
        font-style: italic;
        text-align: center;
    }
    </style>
    <p class="app-description">
        Explore tools for calculations, weather updates, and the latest news.  
        
    </p>
    """,
    unsafe_allow_html=True
)

selected_tool = st.sidebar.selectbox(
    "Avalible TOOLs:", 
    ["None", "Calculator", "Weather", "News","google_search"]
)
user_input = st.text_input("Enter your query")


if st.button("Submit", key="process_data",):
    response = agent.invoke(user_input)
    st.write(response)
    st.write("Let me know if you want more 😊")