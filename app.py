import os
from datetime import date, timedelta

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Travel Planner Agent",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ AI Travel Planner Agent")
st.write("Plan your next adventure with personalized AI travel recommendations.")

# Read credentials from the environment
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
model_name = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
).strip()

with st.sidebar:
    st.header("🌍 Plan Your Trip")
    destination = st.text_input("Destination", "Hyderabad to Goa")
    start_date = st.date_input(
        "Start Date",
        date.today() + timedelta(days=7)
    )
    end_date = st.date_input(
        "End Date",
        date.today() + timedelta(days=10)
    )
    travelers = st.number_input(
        "Number of Travelers", 1, 30, 2
    )
    budget = st.number_input(
        "Total Budget (₹)",
        min_value=1000,
        value=25000,
        step=1000
    )
    style = st.selectbox(
        "Travel Style",
        ["Budget", "Mid-range", "Luxury"]
    )
    interests = st.multiselect(
        "Interests",
        [
            "Nature", "Adventure", "Beaches", "Food",
            "Culture", "Shopping", "History", "Nightlife",
            "Family activities"
        ],
        default=["Nature", "Food", "Culture"]
    )

st.subheader("🧭 Your Personalized Travel Itinerary")

special_requests = st.text_area(
    "Additional preferences",
    placeholder=(
        "Example: vegetarian food, public transport, "
        "famous local attractions..."
    )
)

if st.button("✨ Generate My Travel Plan", type="primary"):
    if not api_key:
        st.error(
            "GEMINI_API_KEY is missing from the Streamlit process. "
            "Load your Colab Secret before starting Streamlit."
        )
    elif not destination.strip():
        st.warning("Please enter a destination.")
    elif end_date < start_date:
        st.warning("End date must be on or after the start date.")
    else:
        days = (end_date - start_date).days + 1

        prompt = f"""
You are an expert travel planning assistant.

Create a practical travel itinerary using these details:
Destination/route: {destination}
Start date: {start_date}
End date: {end_date}
Duration: {days} days
Travelers: {travelers}
Total group budget: INR {budget}
Travel style: {style}
Interests: {", ".join(interests) if interests else "General sightseeing"}
Additional preferences: {special_requests or "None"}

Return a well-organized Markdown travel plan containing:
1. Trip overview and assumptions.
2. Day-by-day itinerary with morning, afternoon, and evening activities.
3. Suggested attractions and activities.
4. Food and restaurant suggestions.
5. Estimated budget breakdown in INR.
6. Transport and accommodation suggestions.
7. Practical travel tips and a packing checklist.

Keep the plan within the stated budget where reasonably possible.
Calculate the duration from the dates. Flag uncertain costs.
Do not claim to have checked live flight prices, hotel availability,
weather, or opening hours unless verified by a live data source.
"""

        with st.spinner("Planning your trip..."):
            try:
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.5
                    )
                )

                if response.text:
                    st.session_state["trip_plan"] = response.text
                    st.session_state["trip_destination"] = destination
                else:
                    st.error("The AI returned an empty response.")

            except Exception as exc:
                error_text = str(exc)
                st.error(f"Could not generate itinerary: {error_text}")

                if "401" in error_text or "UNAUTHENTICATED" in error_text:
                    st.info(
                        "Authentication failed. Reload the valid "
                        "GEMINI_API_KEY from Colab Secrets and restart "
                        "Streamlit. Never print or share the key."
                    )
                elif "403" in error_text or "PERMISSION_DENIED" in error_text:
                    st.info(
                        "Check API key permissions and project access."
                    )
                elif "404" in error_text or "NOT_FOUND" in error_text:
                    st.info(
                        f"Model '{model_name}' was not found or is "
                        "unavailable to this API key. Verify the exact "
                        "model ID using client.models.list()."
                    )
                elif "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    st.info(
                        "The API quota or rate limit may be exhausted. "
                        "Check your usage and limits in Google AI Studio."
                    )
                elif "503" in error_text or "UNAVAILABLE" in error_text:
                    st.info(
                        "The model is temporarily unavailable. Retry "
                        "later or test another available text model."
                    )
                else:
                    st.info(
                        "Check the error details and confirm that the "
                        "selected model supports text generation."
                    )

if "trip_plan" in st.session_state:
    st.divider()
    st.subheader(
        f"🗺️ Your Trip to {st.session_state['trip_destination']}"
    )
    st.markdown(st.session_state["trip_plan"])

    st.download_button(
        "📥 Download Itinerary",
        data=st.session_state["trip_plan"],
        file_name="travel_itinerary.md",
        mime="text/markdown"
    )

st.divider()
st.caption(
    "AI-generated recommendations may need verification before booking."
)
