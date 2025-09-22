# from django.http import JsonResponse
# from sklearn.linear_model import LinearRegression
# import numpy as np
# import pandas as pd
#
# from attendance_tracker.models import Attendance
#
#
# def insights(request):
#     # Query attendance data
#     data = Attendance.objects.filter(center=request.user).values('student_id', 'time', 'status')
#     df = pd.DataFrame.from_records(data)
#
#     if df.empty:
#         return JsonResponse({"error": "⚠️ No attendance data found"})
#
#     # Ensure datetime for 'time'
#     df['time'] = pd.to_datetime(df['time'], errors='coerce')
#
#     # Convert status to numeric (0/1)
#     if df['status'].dtype == object:
#         df['present'] = df['status'].map({"Present": 1, "Absent": 0})
#     else:
#         df['present'] = df['status'].astype(int)
#
#     # Weekly average attendance (ISO calendar week)
#     weekly = df.groupby(df["time"].dt.isocalendar().week)['present'].mean() * 100
#
#     # Prepare regression data
#     X = np.arange(len(weekly)).reshape(-1, 1)   # model step index
#     y = weekly.values
#
#     model = LinearRegression().fit(X, y)
#
#     # Predict for the next week
#     model_step_next = len(weekly)                       # next step in regression model
#     iso_week_next = weekly.index.max() + 1              # actual calendar week number
#     pred = model.predict([[model_step_next]])[0]
#
#     return JsonResponse({
#         "model_step": int(model_step_next + 1),          # step index (1-based)
#         "iso_week_number": int(iso_week_next),           # real ISO week
#         "predicted_attendance_rate": float(pred),
#     })

from vertexai import generative_models

import vertexai

from attendance_tracker.models import Attendance

vertexai.init(project="zedtrack-ai-assistant", location="us-central1")

model = generative_models.GenerativeModel("gemini-2.5-flash-lite")

def insights(request):
    records = Attendance.objects.values("student", "time", "status", "id")

    data_text =  "\n".join([f"{r['student']} ({r['id']}) - {r['time']} - {r['status']}" for r in records])

    prompt = f"""
    Here is attendance data:
    {data_text}

    Please calculate:
    1. Highlight students with attendance below 70%.
    2. Predicted attendance rate for the next week.
    3. Then, compare last and next week attendance rates.
    4. And, give essential highlights.
        
    Keep outcomes as short as possible and concise. Highlight important numbers with <b></b>.
    
    Here is the format:
    <b>Attendance report:</b><br>
    <span style="color: var(--main-color);"><b>-</b></span> Attendance rate for last week: <span style="color: var(--main-color);"><b>(percentage)</b></span><br>
    <span style="color: var(--main-color);"><b>-</b></span> Predicted attendance rate for next week: <span style="color: var(--main-color);"><b>(percentage)</b></span><br>
    <span style="color: var(--main-color);"><b>-</b></span> Attendance rate increased by <span style="color: var(--main-color);"><b>(percentage)</b></span> compared to last week.
    <br><br>
    <b>Essential highlights:</b><br>
    <span style="color: var(--main-color);"><b>-</b></span> first highlight.<br>
    <span style="color: var(--main-color);"><b>-</b></span> second highlight.<br>
    <span style="color: var(--main-color);"><b>-</b></span> third highlight.<br>
    
    Don't give any comments or words, just give data in the format I gave.
    """

    response = model.generate_content(prompt)
    return response.text
