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
    visualize_student_schedules
)

# --- COURSE DATA DEFINITION ---
# Comprehensive list of courses with lecturer, credits, and room requirements
COURSE_DATA = {
    'MK01-A': {'lecturer': 'D01', 'credits': 3, 'required_room': 'R01', 'class': 'A'},
    'MK01-B': {'lecturer': 'D01', 'credits': 3, 'required_room': 'R01', 'class': 'B'},
    'MK02-A': {'lecturer': 'D02', 'credits': 3, 'required_room': 'R02', 'class': 'A'},
    'MK02-B': {'lecturer': 'D02', 'credits': 3, 'required_room': 'R02', 'class': 'B'},
    'MK03-A': {'lecturer': 'D03', 'credits': 3, 'required_room': 'R03', 'class': 'A'},
    'MK03-B': {'lecturer': 'D03', 'credits': 3, 'required_room': 'R03', 'class': 'B'},
    'MK04-A': {'lecturer': 'D04', 'credits': 3, 'required_room': 'R04', 'class': 'A'},
    'MK04-B': {'lecturer': 'D04', 'credits': 3, 'required_room': 'R04', 'class': 'B'},
    'MK05-A': {'lecturer': 'D05', 'credits': 3, 'required_room': 'R05', 'class': 'A'},
    'MK05-B': {'lecturer': 'D05', 'credits': 3, 'required_room': 'R05', 'class': 'B'},
    'MK06-A': {'lecturer': 'D06', 'credits': 3, 'required_room': 'R06', 'class': 'A'},
    'MK06-B': {'lecturer': 'D06', 'credits': 3, 'required_room': 'R06', 'class': 'B'},
    'MK07-A': {'lecturer': 'D07', 'credits': 3, 'required_room': 'R07', 'class': 'A'},
    'MK07-B': {'lecturer': 'D07', 'credits': 3, 'required_room': 'R07', 'class': 'B'},
    'MK08-A': {'lecturer': 'D08', 'credits': 3, 'required_room': 'R08', 'class': 'A'},
    'MK08-B': {'lecturer': 'D08', 'credits': 3, 'required_room': 'R08', 'class': 'B'},
    'MK09-A': {'lecturer': 'D09', 'credits': 3, 'required_room': 'R09', 'class': 'A'},
    'MK09-B': {'lecturer': 'D09', 'credits': 3, 'required_room': 'R09', 'class': 'B'},
    'MK10-A': {'lecturer': 'D10', 'credits': 3, 'required_room': 'R10', 'class': 'A'},
    'MK10-B': {'lecturer': 'D10', 'credits': 3, 'required_room': 'R10', 'class': 'B'},
    'MK11-A': {'lecturer': 'D11', 'credits': 3, 'required_room': 'R01', 'class': 'A'}, 
    'MK11-B': {'lecturer': 'D11', 'credits': 3, 'required_room': 'R01', 'class': 'B'},
    'MK12-A': {'lecturer': 'D12', 'credits': 3, 'required_room': 'R02', 'class': 'A'}, 
    'MK12-B': {'lecturer': 'D12', 'credits': 3, 'required_room': 'R02', 'class': 'B'},
    'MK13-A': {'lecturer': 'D13', 'credits': 4, 'required_room': 'R03', 'class': 'A'}, 
    'MK13-B': {'lecturer': 'D13', 'credits': 4, 'required_room': 'R03', 'class': 'B'},
    'MK14-A': {'lecturer': 'D14', 'credits': 4, 'required_room': 'R04', 'class': 'A'}, 
    'MK14-B': {'lecturer': 'D14', 'credits': 4, 'required_room': 'R04', 'class': 'B'},
    'MK15-A': {'lecturer': 'D15', 'credits': 4, 'required_room': 'R05', 'class': 'A'}, 
    'MK15-B': {'lecturer': 'D15', 'credits': 4, 'required_room': 'R05', 'class': 'B'},
    'MK16-A': {'lecturer': 'D01', 'credits': 4, 'required_room': 'R06', 'class': 'A'}, 
    'MK16-B': {'lecturer': 'D01', 'credits': 4, 'required_room': 'R06', 'class': 'B'},
    'MK17-A': {'lecturer': 'D02', 'credits': 4, 'required_room': 'R07', 'class': 'A'}, 
    'MK17-B': {'lecturer': 'D02', 'credits': 4, 'required_room': 'R07', 'class': 'B'},
    'MK18-A': {'lecturer': 'D03', 'credits': 4, 'required_room': 'R08', 'class': 'A'}, 
    'MK18-B': {'lecturer': 'D03', 'credits': 4, 'required_room': 'R08', 'class': 'B'},
    'MK19': {'lecturer': 'D04', 'credits': 5, 'required_room': 'R09', 'class': 'Joint'}, 
    'MK20': {'lecturer': 'D05', 'credits': 5, 'required_room': 'R10', 'class': 'Joint'},
    'MK21': {'lecturer': 'D06', 'credits': 5, 'required_room': 'R01', 'class': 'Joint'},
    'MK22': {'lecturer': 'D07', 'credits': 5, 'required_room': 'R02', 'class': 'Joint'},
    'MK23': {'lecturer': 'D08', 'credits': 5, 'required_room': 'R03', 'class': 'Joint'},
    'MK24': {'lecturer': 'D09', 'credits': 5, 'required_room': 'R04', 'class': 'Joint'},
    'MK25': {'lecturer': 'D10', 'credits': 5, 'required_room': 'R05', 'class': 'Joint'},
    'MK26': {'lecturer': 'D11', 'credits': 5, 'required_room': 'R06', 'class': 'Joint'},
    'MK27': {'lecturer': 'D12', 'credits': 5, 'required_room': 'R07', 'class': 'Joint'},
    'MK28': {'lecturer': 'D13', 'credits': 5, 'required_room': 'R08', 'class': 'Joint'},
    'MK29': {'lecturer': 'D14', 'credits': 5, 'required_room': 'R09', 'class': 'Joint'},
    'MK30': {'lecturer': 'D15', 'credits': 5, 'required_room': 'R10', 'class': 'Joint'},
}
# Import data from file
with open('courses.json', 'r') as file:
    COURSE_DATA = json.load(file)

# --- STUDENT ENROLLMENT DATA ---
# Mapping of students to their respective sets of enrolled courses
STUDENT_DATA = {
    'MHS101': {'MK01-A', 'MK02-A', 'MK03-A', 'MK04-A', 'MK13-A', 'MK14-A'},
    'MHS102': {'MK05-B', 'MK06-B', 'MK07-B', 'MK08-B', 'MK15-B', 'MK16-B'},
    'MHS103': {'MK09-A', 'MK10-A', 'MK17-A', 'MK19', 'MK20'}, 
    'MHS104': {'MK11-B', 'MK12-B', 'MK18-B', 'MK21', 'MK22'}, 
    'MHS105': {'MK13-A', 'MK15-A', 'MK23', 'MK24'},
    'MHS106': {'MK14-B', 'MK16-B', 'MK25', 'MK26'}, 
    'MHS107': {'MK27', 'MK29'},
    'MHS108': {'MK28', 'MK30'},
}
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
    
    print("\n[DISPLAY] University Master Matrix:")
    visualize_schedule_matrix(graph, final_schedule) 
    
    print("\n[DISPLAY] Individual Student Timetables:")
    visualize_student_schedules(STUDENT_DATA, final_schedule, graph)

    print("\n================================================")
    print("=== PROCESS COMPLETE. CHECK 'output/' FOLDER ===")
    print("================================================")

if __name__ == '__main__':
    run_scheduling_process()