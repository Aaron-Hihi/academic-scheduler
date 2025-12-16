import networkx as nx
from graph_core import (
    create_scheduling_graph,
    standard_greedy_coloring,
    equitable_coloring_optimized,
    calculate_daily_load,
    create_conflict_graph_old # For comparison/logging only
)
from visualization import (
    visualize_conflict_graph,
    visualize_colored_graph,
    visualize_sks_load,
    visualize_schedule_matrix,
    visualize_student_schedule
)

MK_INTI_DEFINITION = {
    'MK01': {'dosen': 'D01', 'sks': 3, 'ruang_tuntut': 'R01'}, 'MK02': {'dosen': 'D02', 'sks': 3, 'ruang_tuntut': 'R02'},
    'MK03': {'dosen': 'D03', 'sks': 3, 'ruang_tuntut': 'R03'}, 'MK04': {'dosen': 'D04', 'sks': 3, 'ruang_tuntut': 'R04'},
    'MK05': {'dosen': 'D05', 'sks': 3, 'ruang_tuntut': 'R05'}, 'MK06': {'dosen': 'D06', 'sks': 3, 'ruang_tuntut': 'R06'},
    'MK07': {'dosen': 'D07', 'sks': 3, 'ruang_tuntut': 'R07'}, 'MK08': {'dosen': 'D08', 'sks': 3, 'ruang_tuntut': 'R08'},
    'MK09': {'dosen': 'D09', 'sks': 3, 'ruang_tuntut': 'R09'}, 'MK10': {'dosen': 'D10', 'sks': 3, 'ruang_tuntut': 'R10'},
    
    'MK11': {'dosen': 'D01', 'sks': 2, 'ruang_tuntut': 'R01'}, 'MK12': {'dosen': 'D02', 'sks': 2, 'ruang_tuntut': 'R02'},
    'MK13': {'dosen': 'D03', 'sks': 2, 'ruang_tuntut': 'R03'}, 'MK14': {'dosen': 'D04', 'sks': 2, 'ruang_tuntut': 'R04'},
    'MK15': {'dosen': 'D05', 'sks': 2, 'ruang_tuntut': 'R05'}, 
    
    'MK16': {'dosen': 'D06', 'sks': 4, 'ruang_tuntut': 'R06'}, 'MK17': {'dosen': 'D07', 'sks': 4, 'ruang_tuntut': 'R07'},
    'MK18': {'dosen': 'D08', 'sks': 4, 'ruang_tuntut': 'R08'}, 'MK19': {'dosen': 'D09', 'sks': 4, 'ruang_tuntut': 'R09'},
    'MK20': {'dosen': 'D10', 'sks': 4, 'ruang_tuntut': 'R10'},
    
    'MK21': {'dosen': 'D01', 'sks': 5, 'ruang_tuntut': 'R01'}, 'MK22': {'dosen': 'D02', 'sks': 5, 'ruang_tuntut': 'R02'},
    'MK23': {'dosen': 'D03', 'sks': 5, 'ruang_tuntut': 'R03'}, 'MK24': {'dosen': 'D04', 'sks': 5, 'ruang_tuntut': 'R04'},
    'MK25': {'dosen': 'D05', 'sks': 5, 'ruang_tuntut': 'R05'}
}

data_matkul = {
    # ---------------- 3 SKS (Reguler: A & B) ----------------
    'MK01-A': {'dosen': 'D01', 'sks': 3, 'ruang_tuntut': 'R01', 'kelas': 'A'},
    'MK01-B': {'dosen': 'D01', 'sks': 3, 'ruang_tuntut': 'R01', 'kelas': 'B'},
    'MK02-A': {'dosen': 'D02', 'sks': 3, 'ruang_tuntut': 'R02', 'kelas': 'A'},
    'MK02-B': {'dosen': 'D02', 'sks': 3, 'ruang_tuntut': 'R02', 'kelas': 'B'},
    'MK03-A': {'dosen': 'D03', 'sks': 3, 'ruang_tuntut': 'R03', 'kelas': 'A'},
    'MK03-B': {'dosen': 'D03', 'sks': 3, 'ruang_tuntut': 'R03', 'kelas': 'B'},
    'MK04-A': {'dosen': 'D04', 'sks': 3, 'ruang_tuntut': 'R04', 'kelas': 'A'},
    'MK04-B': {'dosen': 'D04', 'sks': 3, 'ruang_tuntut': 'R04', 'kelas': 'B'},
    'MK05-A': {'dosen': 'D05', 'sks': 3, 'ruang_tuntut': 'R05', 'kelas': 'A'},
    'MK05-B': {'dosen': 'D05', 'sks': 3, 'ruang_tuntut': 'R05', 'kelas': 'B'},
    'MK06-A': {'dosen': 'D06', 'sks': 3, 'ruang_tuntut': 'R06', 'kelas': 'A'},
    'MK06-B': {'dosen': 'D06', 'sks': 3, 'ruang_tuntut': 'R06', 'kelas': 'B'},
    'MK07-A': {'dosen': 'D07', 'sks': 3, 'ruang_tuntut': 'R07', 'kelas': 'A'},
    'MK07-B': {'dosen': 'D07', 'sks': 3, 'ruang_tuntut': 'R07', 'kelas': 'B'},
    'MK08-A': {'dosen': 'D08', 'sks': 3, 'ruang_tuntut': 'R08', 'kelas': 'A'},
    'MK08-B': {'dosen': 'D08', 'sks': 3, 'ruang_tuntut': 'R08', 'kelas': 'B'},
    'MK09-A': {'dosen': 'D09', 'sks': 3, 'ruang_tuntut': 'R09', 'kelas': 'A'},
    'MK09-B': {'dosen': 'D09', 'sks': 3, 'ruang_tuntut': 'R09', 'kelas': 'B'},
    'MK10-A': {'dosen': 'D10', 'sks': 3, 'ruang_tuntut': 'R10', 'kelas': 'A'},
    'MK10-B': {'dosen': 'D10', 'sks': 3, 'ruang_tuntut': 'R10', 'kelas': 'B'},
    'MK11-A': {'dosen': 'D11', 'sks': 3, 'ruang_tuntut': 'R01', 'kelas': 'A'}, 
    'MK11-B': {'dosen': 'D11', 'sks': 3, 'ruang_tuntut': 'R01', 'kelas': 'B'},
    'MK12-A': {'dosen': 'D12', 'sks': 3, 'ruang_tuntut': 'R02', 'kelas': 'A'}, 
    'MK12-B': {'dosen': 'D12', 'sks': 3, 'ruang_tuntut': 'R02', 'kelas': 'B'},

    # ---------------- 4 SKS (Reguler: A & B) ----------------
    'MK13-A': {'dosen': 'D13', 'sks': 4, 'ruang_tuntut': 'R03', 'kelas': 'A'}, 
    'MK13-B': {'dosen': 'D13', 'sks': 4, 'ruang_tuntut': 'R03', 'kelas': 'B'},
    'MK14-A': {'dosen': 'D14', 'sks': 4, 'ruang_tuntut': 'R04', 'kelas': 'A'}, 
    'MK14-B': {'dosen': 'D14', 'sks': 4, 'ruang_tuntut': 'R04', 'kelas': 'B'},
    'MK15-A': {'dosen': 'D15', 'sks': 4, 'ruang_tuntut': 'R05', 'kelas': 'A'}, 
    'MK15-B': {'dosen': 'D15', 'sks': 4, 'ruang_tuntut': 'R05', 'kelas': 'B'},
    'MK16-A': {'dosen': 'D01', 'sks': 4, 'ruang_tuntut': 'R06', 'kelas': 'A'}, 
    'MK16-B': {'dosen': 'D01', 'sks': 4, 'ruang_tuntut': 'R06', 'kelas': 'B'},
    'MK17-A': {'dosen': 'D02', 'sks': 4, 'ruang_tuntut': 'R07', 'kelas': 'A'}, 
    'MK17-B': {'dosen': 'D02', 'sks': 4, 'ruang_tuntut': 'R07', 'kelas': 'B'},
    'MK18-A': {'dosen': 'D03', 'sks': 4, 'ruang_tuntut': 'R08', 'kelas': 'A'}, 
    'MK18-B': {'dosen': 'D03', 'sks': 4, 'ruang_tuntut': 'R08', 'kelas': 'B'},
    
    # ---------------- 5 SKS (Kuliah Umum/Gabungan) ----------------
    'MK19': {'dosen': 'D04', 'sks': 5, 'ruang_tuntut': 'R09', 'kelas': 'Gabungan'}, 
    'MK20': {'dosen': 'D05', 'sks': 5, 'ruang_tuntut': 'R10', 'kelas': 'Gabungan'},
    'MK21': {'dosen': 'D06', 'sks': 5, 'ruang_tuntut': 'R01', 'kelas': 'Gabungan'},
    'MK22': {'dosen': 'D07', 'sks': 5, 'ruang_tuntut': 'R02', 'kelas': 'Gabungan'},
    'MK23': {'dosen': 'D08', 'sks': 5, 'ruang_tuntut': 'R03', 'kelas': 'Gabungan'},
    'MK24': {'dosen': 'D09', 'sks': 5, 'ruang_tuntut': 'R04', 'kelas': 'Gabungan'},
    'MK25': {'dosen': 'D10', 'sks': 5, 'ruang_tuntut': 'R05', 'kelas': 'Gabungan'},
    'MK26': {'dosen': 'D11', 'sks': 5, 'ruang_tuntut': 'R06', 'kelas': 'Gabungan'},
    'MK27': {'dosen': 'D12', 'sks': 5, 'ruang_tuntut': 'R07', 'kelas': 'Gabungan'},
    'MK28': {'dosen': 'D13', 'sks': 5, 'ruang_tuntut': 'R08', 'kelas': 'Gabungan'},
    'MK29': {'dosen': 'D14', 'sks': 5, 'ruang_tuntut': 'R09', 'kelas': 'Gabungan'},
    'MK30': {'dosen': 'D15', 'sks': 5, 'ruang_tuntut': 'R10', 'kelas': 'Gabungan'},
}

data_mahasiswa = {
    # ---------------- Angkatan 2025 (20 SKS) ----------------
    # MHS101 (2025 A): 4x(3 SKS A) + 2x(4 SKS A) = 12 + 8 = 20 SKS
    'MHS101': {'MK01-A', 'MK02-A', 'MK03-A', 'MK04-A', 'MK13-A', 'MK14-A'},
    
    # MHS102 (2025 B): 4x(3 SKS B) + 2x(4 SKS B) = 12 + 8 = 20 SKS
    'MHS102': {'MK05-B', 'MK06-B', 'MK07-B', 'MK08-B', 'MK15-B', 'MK16-B'},
    
    # ---------------- Angkatan 2024 (20 SKS) ----------------
    # MHS103 (2024 A): 2x(3 SKS A) + 1x(4 SKS A) + 2x(5 SKS Gabungan) = 6 + 4 + 10 = 20 SKS
    'MHS103': {'MK09-A', 'MK10-A', 'MK17-A', 'MK19', 'MK20'}, 
    
    # MHS104 (2024 B): 2x(3 SKS B) + 1x(4 SKS B) + 2x(5 SKS Gabungan) = 6 + 4 + 10 = 20 SKS
    'MHS104': {'MK11-B', 'MK12-B', 'MK18-B', 'MK21', 'MK22'}, 
    
    # ---------------- Angkatan 2023 (18 SKS) ----------------
    # MHS105 (2023 A): 2x(4 SKS A) + 2x(5 SKS Gabungan) = 8 + 10 = 18 SKS
    'MHS105': {'MK13-A', 'MK15-A', 'MK23', 'MK24'},
    
    # MHS106 (2023 B): 2x(4 SKS B) + 2x(5 SKS Gabungan) = 8 + 10 = 18 SKS
    'MHS106': {'MK14-B', 'MK16-B', 'MK25', 'MK26'}, 

    # ---------------- Angkatan 2022 (10 SKS) ----------------
    # MHS107 (2022 A): 2x(5 SKS Gabungan) = 10 SKS
    'MHS107': {'MK27', 'MK29'},

    # MHS108 (2022 B): 2x(5 SKS Gabungan) = 10 SKS
    'MHS108': {'MK28', 'MK30'},
}



def run_scheduling_process():
    """Runs the scheduling process: Graph creation, Greedy Coloring, and Equitable Optimization."""
    print("=============================================")
    print("=== STARTING TIMETABLING SCHEDULING SYSTEM ===")
    print("=============================================")

    # --- GRAPH CONSTRUCTION (Based on Student Conflicts) ---
    print("\n--- 1. GRAPH CONSTRUCTION ---")
    G = create_scheduling_graph(data_matkul, data_mahasiswa)

    # Check the structure of the old graph for logging lecturer/room constraints
    G_old = create_conflict_graph_old(data_matkul, data_mahasiswa) 
    
    # Visualize the conflict graph structure
    visualize_conflict_graph(G, 'output/1_conflict_graph.png')
    
    # --- INITIAL GREEDY COLORING ---
    print("\n--- 2. INITIAL GREEDY COLORING (Scheduling) ---")
    
    # Greedy coloring assigns the initial, valid schedule
    initial_coloring = standard_greedy_coloring(G)
    
    if len(initial_coloring) != len(G.nodes):
        print("FATAL ERROR: Initial coloring failed for some courses. Aborting optimization.")
        

    initial_daily_load = calculate_daily_load(G, initial_coloring)
    initial_sks_values = list(initial_daily_load.values())
    initial_mean = sum(initial_sks_values) / len(initial_sks_values)
    initial_variance = sum((x - initial_mean) ** 2 for x in initial_sks_values)
    
    print(f"\n[INITIAL RESULT] Daily Load: {initial_daily_load}. Variance: {initial_variance:.2f}")

    print("\n--- 3. EQUITABLE OPTIMIZATION (Balancing Load) ---")
    
    # Optimize the schedule using MOVE/SWAP heuristics
    final_coloring, final_daily_load = equitable_coloring_optimized(G, initial_coloring)
    
    final_sks_values = list(final_daily_load.values())
    final_mean = sum(final_sks_values) / len(final_sks_values)
    final_variance = sum((x - final_mean) ** 2 for x in final_sks_values)


    print("\n=============================================")
    print("=== FINAL SCHEDULING SUMMARY ===")
    print("=============================================")
    
    # Display Load Comparison
    print(f"Initial Load (SKS): {initial_daily_load}")
    print(f"Final Load (SKS):   {final_daily_load}")
    print(f"Initial Variance: {initial_variance:.2f} | Final Variance: {final_variance:.2f}")

    # Visualize Load
    visualize_sks_load(final_daily_load, 'output/2_final_sks_load.png')
    
    # Visualize the Scheduled Graph
    visualize_colored_graph(G, final_coloring, 'output/3_colored_schedule.png') 

    # Display Matrix Schedule
    visualize_schedule_matrix(G, final_coloring) 

    # Display Student Schedules
    visualize_student_schedule(data_mahasiswa, final_coloring, G)

    print("\nProcess finished. Check the 'output/' directory for saved charts.")

if __name__ == '__main__':
    # Ensure output directory exists
    import os
    if not os.path.exists('output'):
        os.makedirs('output')
        
    run_scheduling_process()