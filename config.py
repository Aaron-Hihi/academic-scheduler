from datetime import datetime, timedelta

# --- GLOBAL CONFIGURATION ---
# Centralized settings for the entire university system
CONFIG = {
    'START_TIME': '07:30',
    'END_LIMIT': '16:40',
    'SLOT_DURATION': 50,
    'DAYS': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
    'STUDENT_WEIGHT': 0.5
}

# --- TIME GENERATION ---
# Logic to generate valid start times based on the config
def generate_available_start_times():
    start = datetime.strptime(CONFIG['START_TIME'], '%H:%M')
    end_limit = datetime.strptime(CONFIG['END_LIMIT'], '%H:%M')
    interval = timedelta(minutes=CONFIG['SLOT_DURATION'])
    
    times = []
    current = start
    while current < end_limit:
        times.append(current.strftime('%H:%M'))
        current += interval
    return times

AVAILABLE_START_TIMES = generate_available_start_times()

# --- TIME MATH UTILITIES ---
# Helper functions for duration and overlap calculations
def get_duration_minutes(credits):
    return credits * CONFIG['SLOT_DURATION']

def get_end_time(start_time_str, duration_minutes):
    start_dt = datetime.strptime(start_time_str, '%H:%M')
    return (start_dt + timedelta(minutes=duration_minutes)).strftime('%H:%M')

def is_within_work_hours(start_time_str, credits):
    duration = get_duration_minutes(credits)
    end_str = get_end_time(start_time_str, duration)
    return datetime.strptime(end_str, '%H:%M') <= datetime.strptime(CONFIG['END_LIMIT'], '%H:%M')

def time_intervals_overlap(start1, end1, start2, end2):
    s1, e1 = datetime.strptime(start1, '%H:%M'), datetime.strptime(end1, '%H:%M')
    s2, e2 = datetime.strptime(start2, '%H:%M'), datetime.strptime(end2, '%H:%M')
    return max(s1, s2) < min(e1, e2)