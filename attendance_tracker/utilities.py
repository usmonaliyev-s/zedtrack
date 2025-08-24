from django.http import JsonResponse
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd

from attendance_tracker.models import *

def insights(request):
    data = Attendance.objects.filter(center=request.user).values('student_id', 'time', 'status')
    df = pd.DataFrame.from_records(data)
    if df.empty:
        return JsonResponse({"error": "⚠️ No attendance data found"})
    df['present'] = df['status'].astype(int)

    weekly = df.groupby(df["time"].dt.isocalendar().week)['present'].mean() * 100

    X = np.array(range(len(weekly))).reshape(-1, 1)
    y = weekly.values

    model = LinearRegression()
    model.fit(X, y)

    next_week = len(weekly)
    pred = model.predict([[next_week]])

    return JsonResponse({"week": next_week + 1, "predicted_attendance_rate": float(pred[0]),})