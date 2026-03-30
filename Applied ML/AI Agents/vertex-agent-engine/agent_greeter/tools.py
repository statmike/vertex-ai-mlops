"""Tools for the greeter agent."""

from datetime import datetime, timezone


def get_greeting() -> dict:
    """Get a time-appropriate greeting message.

    Returns:
        A dict with the greeting and current time info.
    """
    now = datetime.now(tz=timezone.utc)
    hour = now.hour

    if hour < 12:
        greeting = "Good morning"
        period = "morning"
    elif hour < 17:
        greeting = "Good afternoon"
        period = "afternoon"
    else:
        greeting = "Good evening"
        period = "evening"

    return {
        "greeting": greeting,
        "period": period,
        "utc_time": now.strftime("%H:%M UTC"),
    }
