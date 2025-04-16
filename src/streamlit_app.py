# streamlit_app.py
import streamlit as st
import boto3
import pandas as pd
import requests
import datetime
import s3_uploader
import json
import os

st.title("📸 FitTrack - Fitness Progress Tracker")

image = st.file_uploader("Upload Progress Photo", type=["jpg", "jpeg", "png"])
if image:
    with open(f"{image.name}", "wb") as f:
        f.write(image.getbuffer())
    s3_uploader.main(f"{image.name}")    
    os.remove(image.name)
    st.success(f"Image {image.name} uploaded!")

st.subheader("Log Your Fitness Data")
weight = st.number_input("Weight (lbs)", min_value=0.0)
stepcount = st.number_input("Daily Stepcount", min_value=0.0)
workout = st.text_input("Workout Description")
date = st.date_input("Date", value=datetime.date.today())

if st.button("Submit Log"):
    payload = {
        "date": str(date),
        "weight": weight,
        "stepcount": stepcount,
        "workout": workout,
        "image_filename": image.name if image else None
    }
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"fitness_data_{current_time}.json", "w") as f:
        json.dump(payload, f)

    s3_uploader.main(f"fitness_data_{current_time}.json")
    os.remove(f"fitness_data_{current_time}.json")
    st.success("Fitness data logged!")

