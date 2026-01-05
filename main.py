import os
import json
from graph_core import (
    create_scheduling_graph,
    standard_greedy_coloring,
    equitable_coloring_optimized,
    calculate_daily_load
)
from visualization import (
    visualize_conflict_graph,
    visualize_colored_graph,
    visualize_credits_load,
    visualize_schedule_matrix,
    visualize_student_schedules,
    export_student_schedules_to_csv,
    export_to_excel
)

# --- COURSE DATA DEFINITION ---
# Comprehensive list of courses with lecturer, credits, and room requirements
# Import data from file
with open('courses.json', 'r') as file:
    COURSE_DATA = json.load(file)

# --- STUDENT ENROLLMENT DATA ---
# Mapping of students to their respective sets of enrolled courses
# Import data
with open('curriculum.json', 'r') as file:
    raw_data = json.load(file)
    STUDENT_DATA = {batch: set(subjects) for batch, subjects in raw_data.items()}

# --- MAIN EXECUTION LOGIC ---
# Orchestrates the scheduling workflow with clear step-by-step progress logging
def run_scheduling_process():
    print("=============================================")
    print("=== STARTING UNIVERSITY SCHEDULING SYSTEM ===")
    print("=============================================")

    if not os.path.exists('output'):
        print("[System] Creating output directory...")
        os.makedirs('output')

    print("\n--- 1. GRAPH CONSTRUCTION ---")
    
    # Check if all subjects in curriculum actually exist in course data
    for batch, subjects in STUDENT_DATA.items():
        for s in subjects:
            if s not in COURSE_DATA:
                print(f"[Error] Subject '{s}' in {batch} not found in COURSE_DATA keys!")
    
    graph = create_scheduling_graph(COURSE_DATA, STUDENT_DATA)
    visualize_conflict_graph(graph, 'output/1_conflict_graph.png')
    print(f"[Log] Graph built with {len(graph.nodes)} nodes and {len(graph.edges)} conflict edges.")

    print("\n--- 2. INITIAL SCHEDULING (GREEDY COLORING) ---")
    initial_schedule = standard_greedy_coloring(graph)
    
    if len(initial_schedule) != len(graph.nodes):
        print("[Fatal] Could not schedule all courses. Terminating process.")
        return

    initial_load = calculate_daily_load(graph, initial_schedule)
    print(f"[Log] Initial scheduling complete. Daily credit counts: {initial_load}")

    print("\n--- 3. LOAD BALANCING OPTIMIZATION ---")
    final_schedule, final_load = equitable_coloring_optimized(graph, initial_schedule, STUDENT_DATA)

    print("\n--- 4. FINALIZING REPORTS ---")
    visualize_credits_load(final_load, 'output/2_final_credits_load.png')
    visualize_colored_graph(graph, final_schedule, 'output/3_colored_schedule.png') 
    
    # output to csv file
    export_student_schedules_to_csv(STUDENT_DATA, final_schedule, graph, 'output/student_timetables.csv')
    
    # Export to excel file
    export_to_excel(STUDENT_DATA, final_schedule, graph, COURSE_DATA)
    
    print("\n[DISPLAY] University Master Matrix:")
    visualize_schedule_matrix(graph, final_schedule) 
    
    print("\n[DISPLAY] Individual Student Timetables:")
    visualize_student_schedules(STUDENT_DATA, final_schedule, graph)

    print("\n================================================")
    print("=== PROCESS COMPLETE. CHECK 'output/' FOLDER ===")
    print("================================================")

if __name__ == '__main__':
    run_scheduling_process()