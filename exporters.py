import os
import csv
from config import CONFIG, AVAILABLE_START_TIMES, get_duration_minutes, get_end_time

# EXPORT LOGIC: GENERATE SORTED MASTER SCHEDULE
def export_master_csv(graph, coloring_result, filename='output/master_schedule.csv'):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        day_order = {day: i for i, day in enumerate(CONFIG['DAYS'])}
        master_data = []

        for course, (day, start) in coloring_result.items():
            node = graph.nodes[course]
            end = get_end_time(start, get_duration_minutes(node['credits']))
            master_data.append({
                'Course': course, 'Day': day, 'Start': start, 'End': end,
                'Lecturer': node['lecturer'], 'Room': node['room'], 
                'SKS': node['credits'], 'day_idx': day_order.get(day, 99)
            })

        master_data.sort(key=lambda x: (x['day_idx'], x['Start']))

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Course', 'Day', 'Start', 'End', 'Lecturer', 'Room', 'SKS'])
            for row in master_data:
                writer.writerow([row['Course'], row['Day'], row['Start'], row['End'], row['Lecturer'], row['Room'], row['SKS']])
        
        print(f"[Success] Master schedule exported: {filename}")
    except Exception as e:
        print(f"[Error] Master export failed: {e}")

# EXPORT LOGIC: GENERATE STUDENT TIMETABLES WITH SKS BLOCKS
def export_individual_schedules(graph, coloring_result, student_data, folder='output/student_schedules'):
    try:
        os.makedirs(folder, exist_ok=True)
        days, times = CONFIG['DAYS'], AVAILABLE_START_TIMES

        for sid, courses in student_data.items():
            grid = {t: {d: "" for d in days} for t in times}
            for c in courses:
                if c in coloring_result:
                    day, start = coloring_result[c]
                    node = graph.nodes[c]
                    start_idx = times.index(start)
                    for i in range(node['credits']):
                        if start_idx + i < len(times):
                            label = f"[START] {c} ({node['room']})" if i == 0 else f"[{c} Cont.]"
                            grid[times[start_idx + i]][day] = label

            with open(f"{folder}/{sid}_schedule.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Time', *days])
                for t in times:
                    writer.writerow([t, *[grid[t][d] for d in days]])
        
        print(f"[Success] Student schedules exported to {folder}/")
    except Exception as e:
        print(f"[Error] Student export failed: {e}")

# EXPORT LOGIC: GENERATE LECTURER TIMETABLES WITH SKS BLOCKS
def export_lecturer_schedules(graph, coloring_result, folder='output/lecturer_schedules'):
    try:
        os.makedirs(folder, exist_ok=True)
        days, times = CONFIG['DAYS'], AVAILABLE_START_TIMES
        
        lecturers = {}
        for course, (day, start) in coloring_result.items():
            lec = graph.nodes[course]['lecturer']
            if lec not in lecturers: lecturers[lec] = []
            平衡_info = (course, day, start)
            lecturers[lec].append(平衡_info)

        for lec_name, assigned_courses in lecturers.items():
            grid = {t: {d: "" for d in days} for t in times}
            for c_code, day, start in assigned_courses:
                node = graph.nodes[c_code]
                start_idx = times.index(start)
                for i in range(node['credits']):
                    if start_idx + i < len(times):
                        label = f"[CLASS] {c_code} ({node['room']})" if i == 0 else f"[{c_code} Cont.]"
                        grid[times[start_idx + i]][day] = label

            clean_name = "".join(x for x in lec_name if x.isalnum() or x in "._- ")
            with open(f"{folder}/{clean_name}_schedule.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Time', *days])
                for t in times:
                    writer.writerow([t, *[grid[t][d] for d in days]])

        print(f"[Success] Lecturer schedules exported to {folder}/")
    except Exception as e:
        print(f"[Error] Lecturer export failed: {e}")