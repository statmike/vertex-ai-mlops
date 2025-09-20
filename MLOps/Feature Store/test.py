from datetime import datetime

def get_current_time_string() -> str:
  """
  Returns a string with the current date and time.
  """
  now = datetime.now()
  formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
  return f"Hey!, the time is current {formatted_time}"

# Example usage:
#print(get_current_time_string())