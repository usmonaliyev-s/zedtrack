from django.http import JsonResponse
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd

from attendance_tracker.models import Attendance


def predicted_attendance(request):
    data = Attendance.objects.filter(center=request.user).values('student_id', 'time', 'status')
    df = pd.DataFrame.from_records(data)

    if df.empty:
        return JsonResponse({"error": "⚠️ No attendance data found"})

    df['time'] = pd.to_datetime(df['time'], errors='coerce')

    if df['status'].dtype == object:
        df['present'] = df['status'].map({"Present": 1, "Absent": 0})
    else:
        df['present'] = df['status'].astype(int)

    weekly = df.groupby(df["time"].dt.isocalendar().week)['present'].mean() * 100

    X = np.arange(len(weekly)).reshape(-1, 1)   # model step index
    y = weekly.values

    model = LinearRegression().fit(X, y)

    model_step_next = len(weekly)                       # next step in regression model
    iso_week_next = weekly.index.max() + 1              # actual calendar week number
    pred = model.predict([[model_step_next]])[0]
    last_week_rate = weekly.iloc[-1]

    return [float(pred), float(last_week_rate)]

from vertexai import generative_models

import vertexai

from attendance_tracker.models import Attendance

vertexai.init(project="zedtrack-ai-assistant", location="us-central1")

model = generative_models.GenerativeModel("gemini-2.5-flash-lite")

def insights(request):
    records = Attendance.objects.filter(center=request.user).values("student", "time", "status", "id")

    data_text =  "\n".join([f"{r['student']} ({r['id']}) - {r['time']} - {r['status']}" for r in records])
    print(predicted_attendance(request))
    prompt = f"""
    You are an assistant that analyzes attendance data. 
    ONLY use the data below, do not invent or assume values.
    
    Here is attendance data:
    {data_text}
    
    Tasks:
    1. Highlight students with attendance below 70% in last 4 records.
    4. Give essential highlights.
    
    Rules:
    - Use ONLY the attendance data provided.
    - Do not add extra comments or make up information.
    - If data is missing, say "Not enough data".
    - Don't change the percentages ({round(predicted_attendance(request)[0], 2)} and {round(predicted_attendance(request)[1], 2)}), which are provided in the text.
    - Follow exactly this format:
    
    <b>Attendance report:</b><br>
    <span style="color: var(--main-color);"><b>-</b></span> Attendance rate for last week: <span style="color: var(--main-color);"><b>{round(predicted_attendance(request)[1], 2)}%</b></span><br>
    <span style="color: var(--main-color);"><b>-</b></span> Predicted attendance rate for next week: <span style="color: var(--main-color);"><b>{round(predicted_attendance(request)[0], 2)}%</b></span><br>
    <b>Essential highlights:</b><br>
    <span style="color: var(--main-color);"><b>-</b></span> first highlight.<br>
    <span style="color: var(--main-color);"><b>-</b></span> second highlight.<br>
    <span style="color: var(--main-color);"><b>-</b></span> third highlight.<br>
    """

    response = model.generate_content(prompt)
    return response.text
