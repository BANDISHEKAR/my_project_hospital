"""Date/time helpers for doctor availability and appointment token timings."""

from datetime import datetime, timedelta

DAY_MAP = {
    "Monday": "Mon",
    "Tuesday": "Tue",
    "Wednesday": "Wed",
    "Thursday": "Thu",
    "Friday": "Fri",
    "Saturday": "Sat",
    "Sunday": "Sun",
}

DAY_ORDER = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6, "Sun": 7}


def get_day_name(date_obj) -> str:
    return DAY_MAP[date_obj.strftime("%A")]


def parse_12hr_time(value: str) -> datetime:
    return datetime.strptime(value.strip().upper(), "%I:%M %p")


def format_12hr_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p")


def calculate_token_time(start_time: str, end_time: str, max_patients: int, token_no: int) -> str:
    start_dt = parse_12hr_time(start_time)
    end_dt = parse_12hr_time(end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    total_minutes = int((end_dt - start_dt).total_seconds() // 60)
    interval = max(1, total_minutes // max_patients)
    appointment_dt = start_dt + timedelta(minutes=(token_no - 1) * interval)
    return format_12hr_time(appointment_dt)
