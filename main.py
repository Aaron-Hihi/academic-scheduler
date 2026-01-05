import os
import json
from exporters import export_master_csv, export_individual_schedules, export_lecturer_schedules
from graph_core import (
    create_scheduling_graph,
    standard_greedy_coloring,
    equitable_coloring_optimized
)
from visualization import (
    visualize_conflict_graph,
    visualize_colored_graph,
    visualize_credits_load,
    visualize_schedule_matrix,
    visualize_student_schedules
)

# DATA PERSISTENCE: JSON STORAGE MANAGER
def manage_json_data(filename, data=None):
    try:
        if data is None:
            if not os.path.exists(filename): return {}
            with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
        with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
        return data
    except Exception as e:
        print(f"[Error] Storage error: {e}")
        return {}

# INTERFACE: BULK DATA ENTRY
def bulk_import_interface():
    print("\n--- BULK IMPORT TOOL ---")
    print("Format: CODE,LECTURER,CREDITS,ROOM (Type 'DONE' to finish)")
    new_courses = {}
    while True:
        line = input("> ").strip()
        if not line or line.upper() == 'DONE': break
        try:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 4: raise ValueError("Fields mismatch")
            code, lec, cred, room = parts
            new_courses[code.upper()] = {'lecturer': lec.upper(), 'credits': int(cred), 'required_room': room.upper()}
        except ValueError:
            print("Invalid format. Use: MK01,D01,3,R01")
    return new_courses

# CORE ENGINE: SCHEDULING WORKFLOW
def run_scheduling_process(courses, students):
    print("\n" + "="*50 + "\nUNIVERSITY SCHEDULING SYSTEM\n" + "="*50)
    if not os.path.exists('output'): os.makedirs('output')

    graph = create_scheduling_graph(courses, students)
    visualize_conflict_graph(graph, 'output/1_conflict_graph.png')
    
    initial_schedule = standard_greedy_coloring(graph)
    if len(initial_schedule) != len(graph.nodes):
        print("[Fatal] Insufficient slots for graph density.")
        return

    final_schedule, final_load = equitable_coloring_optimized(graph, initial_schedule, students)

    # Graphical Reports
    visualize_credits_load(final_load, 'output/2_final_credits_load.png')
    visualize_colored_graph(graph, final_schedule, 'output/3_colored_schedule.png') 
    
    # Console Visualization
    visualize_schedule_matrix(graph, final_schedule) 
    visualize_student_schedules(students, final_schedule, graph)
    
    # CSV Exports (using exporters.py)
    export_master_csv(graph, final_schedule)
    export_individual_schedules(graph, final_schedule, students)
    export_lecturer_schedules(graph, final_schedule)

# MAIN INTERFACE: TERMINAL MENU
def main_terminal_interface():
    courses = manage_json_data('courses.json')
    students = manage_json_data('students.json')

    while True:
        print(f"\nDB: {len(courses)} Courses | {len(students)} Students")
        print("1. Add Course\n2. Bulk Import\n3. Manage Students\n4. Reset DB\n5. RUN SCHEDULER\n6. Exit")
        choice = input("Option: ")

        if choice == '1':
            try:
                code, lec = input("Code: ").upper(), input("Lecturer: ").upper()
                cred, rm = int(input("Credits: ")), input("Room: ").upper()
                courses[code] = {'lecturer': lec, 'credits': cred, 'required_room': rm}
                manage_json_data('courses.json', courses)
            except ValueError: print("Invalid SKS.")
        elif choice == '2':
            courses.update(bulk_import_interface())
            manage_json_data('courses.json', courses)
        elif choice == '3':
            sid = input("Student ID: ").upper()
            codes = input("Course Codes (comma-separated): ").upper().split(',')
            valid = [c.strip() for c in codes if c.strip() in courses]
            students[sid] = list(set(valid))
            manage_json_data('students.json', students)
        elif choice == '4':
            if input("Confirm reset? (y/n): ").lower() == 'y':
                courses, students = {}, {}
                for f in ['courses.json', 'students.json']:
                    if os.path.exists(f): os.remove(f)
        elif choice == '5':
            if courses and students:
                student_sets = {k: set(v) for k, v in students.items()}
                run_scheduling_process(courses, student_sets)
            else: print("Database incomplete.")
        elif choice == '6': break

if __name__ == '__main__':
    main_terminal_interface()