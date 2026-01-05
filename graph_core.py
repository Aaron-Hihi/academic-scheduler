import networkx as nx
from config import (
    CONFIG, 
    AVAILABLE_START_TIMES, 
    get_duration_minutes, 
    get_end_time, 
    is_within_work_hours, 
    time_intervals_overlap
)

# --- GRAPH CONSTRUCTION ---
# Builds a conflict graph where nodes are courses and edges represent scheduling constraints
def create_scheduling_graph(course_data, student_data):
    graph = nx.Graph()
    for course, detail in course_data.items():
        graph.add_node(course, credits=detail['credits'], 
                       lecturer=detail['lecturer'], room=detail['required_room'])

    course_list = list(course_data.keys())
    for i in range(len(course_list)):
        for j in range(i + 1, len(course_list)):
            c1, c2 = course_list[i], course_list[j]
            d1, d2 = course_data[c1], course_data[c2]
            
            reasons = []
            if d1['lecturer'] == d2['lecturer']: reasons.append("Lecturer")
            if d1['required_room'] == d2['required_room']: reasons.append("Room")
            for students in student_data.values():
                if c1 in students and c2 in students:
                    reasons.append("Student")
                    break
            
            if reasons:
                graph.add_edge(c1, c2, reason=", ".join(reasons))
    return graph

# --- PLACEMENT SAFETY ---
# Validates if a specific course can be placed in a slot without violating time or conflict rules
def is_safe_to_place(graph, course, day, start_time, current_schedule):
    if not is_within_work_hours(start_time, graph.nodes[course]['credits']):
        return False

    curr_dur = get_duration_minutes(graph.nodes[course]['credits'])
    curr_end = get_end_time(start_time, curr_dur)

    for neighbor in graph.neighbors(course):
        if neighbor in current_schedule:
            n_day, n_start = current_schedule[neighbor]
            if day == n_day:
                n_dur = get_duration_minutes(graph.nodes[neighbor]['credits'])
                n_end = get_end_time(n_start, n_dur)
                if time_intervals_overlap(start_time, curr_end, n_start, n_end):
                    return False
    return True

# --- INITIAL SCHEDULING ---
# Provides an initial valid coloring using a highest-degree-first greedy approach
def standard_greedy_coloring(graph):
    nodes_sorted = sorted(graph.nodes(), key=lambda n: graph.degree[n], reverse=True)
    result = {}
    
    for course in nodes_sorted:
        placed = False
        for day in CONFIG['DAYS']:
            for start in AVAILABLE_START_TIMES:
                if is_safe_to_place(graph, course, day, start, result):
                    result[course] = (day, start)
                    placed = True
                    break
            if placed: break
        
        if not placed:
            print(f"[Warning] {course} failed to find a slot. Finding conflicting slot...")
            result[course] = (CONFIG['DAYS'][0], AVAILABLE_START_TIMES[0]) 

    return result

# --- LOAD CALCULATIONS ---
# Computes the total credits per day and calculates individual student load variance
def calculate_daily_load(graph, result):
    load = {day: 0 for day in CONFIG['DAYS']}
    for course, (day, _) in result.items():
        load[day] += graph.nodes[course]['credits']
    return load

def calculate_student_load_variance(student_data, result, graph):
    total_var = 0
    if not student_data: return 0
    for courses in student_data.values():
        daily = {day: 0 for day in CONFIG['DAYS']}
        for c in courses:
            if c in result:
                daily[result[c][0]] += graph.nodes[c]['credits']
        mean = sum(daily.values()) / len(CONFIG['DAYS'])
        total_var += sum((x - mean)**2 for x in daily.values())
    return total_var

# --- EQUITABLE OPTIMIZATION ---
# Iteratively improves the schedule with detailed console logging for every improvement
def equitable_coloring_optimized(graph, initial_coloring, student_data=None):
    current = initial_coloring.copy()
    
    def get_score(col):
        load = calculate_daily_load(graph, col)
        mean = sum(load.values()) / len(CONFIG['DAYS'])
        glob_var = sum((x - mean)**2 for x in load.values())
        stud_var = calculate_student_load_variance(student_data, col, graph)
        return glob_var + (CONFIG['STUDENT_WEIGHT'] * stud_var)

    initial_score = get_score(current)
    print(f"\n[STARTING BALANCED OPTIMIZATION]")
    print(f"Initial System Inequity Score: {initial_score:.2f}")

    for i in range(1, 51):
        improved = False
        curr_score = get_score(current)
        
        for node in list(graph.nodes):
            orig_slot = current[node]
            for d in CONFIG['DAYS']:
                for s in AVAILABLE_START_TIMES:
                    if (d, s) == orig_slot: continue
                    
                    if is_safe_to_place(graph, node, d, s, current):
                        current[node] = (d, s)
                        new_score = get_score(current)
                        
                        if new_score < curr_score:
                            print(f" > Step {i}: Moved {node:7} to {d:9} {s} | Score: {new_score:8.2f} (Delta: {curr_score-new_score:5.2f})")
                            curr_score = new_score
                            improved = True
                            break
                        current[node] = orig_slot
                if improved: break
            if improved: break
        
        if not improved:
            print(f"[OPTIMIZATION IDLE] No further improvements found after {i} iterations.")
            break
        
    final_score = get_score(current)
    print(f"Optimization Finished. Final Score: {final_score:.2f} (Total Reduction: {initial_score - final_score:.2f})")
    return current, calculate_daily_load(graph, current)