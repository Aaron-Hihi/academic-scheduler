import networkx as nx
from config import (
    CONFIG, 
    AVAILABLE_START_TIMES, 
    get_duration_minutes, 
    get_end_time, 
    is_within_work_hours, 
    time_intervals_overlap
)

# GRAPH CONSTRUCTION: Builds a conflict network where edges represent resource or student overlaps
def create_scheduling_graph(course_data, student_data):
    graph = nx.Graph()
    for course, detail in course_data.items():
        graph.add_node(course, 
                       credits=detail.get('credits', 0), 
                       lecturer=detail.get('lecturer', 'N/A'), 
                       room=detail.get('required_room', 'N/A'))

    course_list = list(course_data.keys())
    for i in range(len(course_list)):
        for j in range(i + 1, len(course_list)):
            c1, c2 = course_list[i], course_list[j]
            d1, d2 = course_data[c1], course_data[c2]
            
            reasons = []
            if d1.get('lecturer') == d2.get('lecturer'): reasons.append("Lecturer")
            if d1.get('required_room') == d2.get('required_room'): reasons.append("Room")
            
            for students in student_data.values():
                if c1 in students and c2 in students:
                    reasons.append("Student")
                    break
            
            if reasons:
                graph.add_edge(c1, c2, reason=", ".join(reasons))
    return graph

# CONSTRAINT VALIDATION: Checks for time overlaps and resource conflicts with existing neighbors
def is_safe_to_place(graph, course, day, start_time, current_schedule):
    if not is_within_work_hours(start_time, graph.nodes[course].get('credits', 0)):
        return False

    curr_dur = get_duration_minutes(graph.nodes[course].get('credits', 0))
    curr_end = get_end_time(start_time, curr_dur)

    for neighbor in graph.neighbors(course):
        if neighbor in current_schedule:
            n_day, n_start = current_schedule[neighbor]
            if day == n_day:
                n_dur = get_duration_minutes(graph.nodes[neighbor].get('credits', 0))
                n_end = get_end_time(n_start, n_dur)
                if time_intervals_overlap(start_time, curr_end, n_start, n_end):
                    return False
    return True

# INITIAL SCHEDULING: Highest-degree-first greedy coloring to establish a valid baseline
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
            print(f"[Warning] Course {course} could not be placed in any slot.")
            
    return result

# METRICS CALCULATION: Quantifies daily credit loads and student schedule variance
def calculate_daily_load(graph, result):
    load = {day: 0 for day in CONFIG['DAYS']}
    for course, (day, _) in result.items():
        load[day] += graph.nodes[course].get('credits', 0)
    return load

def calculate_student_load_variance(student_data, result, graph):
    total_var = 0
    if not student_data: return 0
    for courses in student_data.values():
        daily = {day: 0 for day in CONFIG['DAYS']}
        for c in courses:
            if c in result:
                daily[result[c][0]] += graph.nodes[c].get('credits', 0)
        mean = sum(daily.values()) / len(CONFIG['DAYS'])
        total_var += sum((x - mean)**2 for x in daily.values())
    return total_var

# EQUITABLE OPTIMIZATION: Iterative local search to minimize global and student load variance
def equitable_coloring_optimized(graph, initial_coloring, student_data=None):
    current = initial_coloring.copy()
    stats = {"move": 0, "swap": 0, "history": []}
    
    def get_score(col):
        load = calculate_daily_load(graph, col)
        mean = sum(load.values()) / len(CONFIG['DAYS'])
        glob_var = sum((x - mean)**2 for x in load.values())
        stud_var = calculate_student_load_variance(student_data, col, graph)
        return glob_var + (CONFIG.get('STUDENT_WEIGHT', 1.0) * stud_var)

    initial_score = get_score(current)
    print(f"\n[STARTING BALANCED OPTIMIZATION - MOVE & SWAP MODE]")
    print(f"Initial System Inequity Score: {initial_score:.2f}")

    for i in range(1, 101):
        improved = False
        curr_score = get_score(current)
        nodes = list(graph.nodes)
        
        for node in nodes:
            orig_day, orig_start = current[node]
            credits = graph.nodes[node].get('credits', 0)
            orig_end = get_end_time(orig_start, get_duration_minutes(credits))
            
            for d in CONFIG['DAYS']:
                for s in AVAILABLE_START_TIMES:
                    if (d, s) == (orig_day, orig_start): continue
                    if is_safe_to_place(graph, node, d, s, current):
                        current[node] = (d, s)
                        new_score = get_score(current)
                        if new_score < curr_score:
                            new_end = get_end_time(s, get_duration_minutes(credits))
                            print(f" > Step {i:2} [MOVE]: {node:12} from {orig_day[:3]} to {d[:3]} {s} | Score: {new_score:.2f}")
                            stats["move"] += 1
                            improved = True
                            break
                        current[node] = (orig_day, orig_start)
                if improved: break
            if improved: break

        if not improved:
            for i_idx in range(len(nodes)):
                for j_idx in range(i_idx + 1, len(nodes)):
                    n1, n2 = nodes[i_idx], nodes[j_idx]
                    slot1, slot2 = current[n1], current[n2]
                    if slot1[0] == slot2[0]: continue
                    
                    temp_sched = current.copy()
                    temp_sched[n1], temp_sched[n2] = slot2, slot1
                    
                    if is_safe_to_place(graph, n1, slot2[0], slot2[1], temp_sched) and \
                       is_safe_to_place(graph, n2, slot1[0], slot1[1], temp_sched):
                        new_score = get_score(temp_sched)
                        if new_score < curr_score:
                            current = temp_sched
                            print(f" > Step {i:2} [SWAP]: {n1:12} <-> {n2:12} | Score: {new_score:.2f}")
                            stats["swap"] += 1
                            improved = True
                            break
                if improved: break

        if not improved:
            print(f"[OPTIMIZATION IDLE] Finished after {i-1} iterations. Moves: {stats['move']}, Swaps: {stats['swap']}")
            break
            
    return current, calculate_daily_load(graph, current)