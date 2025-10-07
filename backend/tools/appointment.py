from datetime import datetime, timedelta
from .calendar_utils import create_calendar_event

def book_appointment(message, service):
    now = datetime.now()
    start = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    return create_calendar_event(
        service=service,
        summary="Doctor Appointment",
        description=message,
        start_time=start.isoformat(),
        end_time=end.isoformat()
    )