import networkx as nx
from datetime import datetime, timedelta

# --- TIME MANAGEMENT & GLOBAL CONSTANTS ---

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

def generate_available_start_times():
    """Generates a list of available class start times (50-minute interval)."""
    start_time = datetime.strptime('07:30', '%H:%M')
    # Latest possible end time for a session to start (not the absolute end of class)
    end_limit = datetime.strptime('19:10', '%H:%M') 
    interval = timedelta(minutes=50)

    times = []
    current_time = start_time
    while current_time <= end_limit:
        times.append(current_time.strftime('%H:%M'))
        current_time += interval
    return times

AVAILABLE_START_TIMES = generate_available_start_times()

def get_duration_minutes(sks):
    """Converts SKS (credit hours) to total duration in minutes (1 SKS = 50 minutes)."""
    return sks * 50

def get_end_time(start_time_str, duration_minutes):
    """Calculates the end time from a start time string and a given duration."""
    dummy_date = datetime.strptime(start_time_str, '%H:%M')
    end_time = dummy_date + timedelta(minutes=duration_minutes)
    return end_time.strftime('%H:%M')

def time_intervals_overlap(start1, end1, start2, end2):
    """Checks if two time intervals (HH:MM) overlap. Uses strict inequality."""
    t1_start = datetime.strptime(start1, '%H:%M')
    t1_end = datetime.strptime(end1, '%H:%M')
    t2_start = datetime.strptime(start2, '%H:%M')
    t2_end = datetime.strptime(end2, '%H:%M')

    # Overlap occurs if Max(Start) < Min(End)
    return max(t1_start, t2_start) < min(t1_end, t2_end)


# --- GRAPH CONSTRUCTION FUNCTIONS ---

def create_conflict_graph_old(data_matkul, data_mahasiswa):
    """
    Creates the Conflict Graph using the OLD logic: 
    Edges caused by conflicts in Students, Lecturers, AND Rooms.
    (Used for comparison only).
    """
    G_old = nx.Graph()
    matkul_list = list(data_matkul.keys())

    for matkul, detail in data_matkul.items():
        G_old.add_node(matkul, sks=detail['sks'], dosen=detail['dosen'], ruangan=detail['ruang_tuntut'])

    for i in range(len(matkul_list)):
        for j in range(i + 1, len(matkul_list)):
            matkul_i = matkul_list[i]
            matkul_j = matkul_list[j]
            detail_i = data_matkul[matkul_i]
            detail_j = data_matkul[matkul_j]
            bentrok_terjadi = False
            alasan_bentrok = []

            # A. Lecturer Conflict (Causes an edge in the OLD model)
            if detail_i['dosen'] == detail_j['dosen']:
                bentrok_terjadi = True
                alasan_bentrok.append("Same Lecturer")

            # B. Room Conflict (Causes an edge in the OLD model)
            if detail_i['ruang_tuntut'] == detail_j['ruang_tuntut']:
                bentrok_terjadi = True
                alasan_bentrok.append("Same Room")

            # C. Student Conflict
            for mhs_matkul_set in data_mahasiswa.values():
                if matkul_i in mhs_matkul_set and matkul_j in mhs_matkul_set:
                    bentrok_terjadi = True
                    alasan_bentrok.append("Student Takes Both")
                    break

            if bentrok_terjadi:
                G_old.add_edge(matkul_i, matkul_j, reason=", ".join(alasan_bentrok))

    print(f"Total Edges in OLD Graph (Lecturer+Room+Student): {len(G_old.edges)}")
    return G_old


def create_scheduling_graph(data_matkul, data_mahasiswa):
    """
    Creates the Conflict Graph (Nodes=Courses, Edges=Student Conflicts ONLY).
    Edges here enforce the Hard Constraint: Matkul must be on different days.
    """
    G = nx.Graph()
    matkul_list = list(data_matkul.keys())

    for matkul, detail in data_matkul.items():
        G.add_node(matkul,
                   sks=detail['sks'],
                   dosen=detail['dosen'],
                   ruangan=detail['ruang_tuntut'])

    for i in range(len(matkul_list)):
        for j in range(i + 1, len(matkul_list)):
            matkul_i = matkul_list[i]
            matkul_j = matkul_list[j]
            bentrok_terjadi = False
            alasan_bentrok = []
        
            # Only check for Student Conflict (Hard Constraint for Graph Coloring)
            for mhs_matkul_set in data_mahasiswa.values():
                if matkul_i in mhs_matkul_set and matkul_j in mhs_matkul_set:
                    bentrok_terjadi = True
                    alasan_bentrok.append("Student Takes Both")
                    break
        
            if bentrok_terjadi:
                G.add_edge(matkul_i, matkul_j, reason=", ".join(alasan_bentrok))
    
    print(f"Total Nodes (Courses): {len(G.nodes)}")
    print(f"Total Edges (Student Conflicts Only): {len(G.edges)}")
    return G


# --- SAFETY CHECK FUNCTION (Constraint Validation) ---

def is_safe_to_place(G, matkul, target_day, target_start_time, current_schedule):
    """
    Checks if a course can be safely placed at the target_day and target_start_time.
    current_schedule: {course: (day, start_time)}
    """
    sks_matkul = G.nodes[matkul]['sks']
    duration = get_duration_minutes(sks_matkul)
    end_time_matkul = get_end_time(target_start_time, duration)

    # Absolute time boundary check (using 19:10 as the latest START time, end time will be later)
    if datetime.strptime(end_time_matkul, '%H:%M') > datetime.strptime('23:00', '%H:%M'):
        return False

    # 1. Check Student Conflicts (Graph Edges / Hard Constraint)
    for neighbor in G.neighbors(matkul):
        if neighbor in current_schedule:
            day_neighbor, _ = current_schedule[neighbor]
            # Student conflict MUST be on different days
            if target_day == day_neighbor: 
                return False 


    # 2. Check Lecturer and Room Time Conflicts (Soft Constraint)
    dosen_matkul = G.nodes[matkul]['dosen']
    ruangan_matkul = G.nodes[matkul]['ruangan']

    for other_matkul, (day_other, start_time_other) in current_schedule.items():
        if other_matkul == matkul:
            continue

        # Only check time conflict if it's on the SAME DAY
        if target_day == day_other:
            sks_other = G.nodes[other_matkul]['sks']
            duration_other = get_duration_minutes(sks_other)
            end_time_other = get_end_time(start_time_other, duration_other)

            # Check if the time intervals overlap
            if time_intervals_overlap(target_start_time, end_time_matkul, start_time_other, end_time_other):
                
                # A. Lecturer Conflict (Same Lecturer cannot teach 2 classes simultaneously)
                if G.nodes[other_matkul]['dosen'] == dosen_matkul:
                    return False # Bentrok dosen pada waktu yang sama

                # B. Room Conflict (Same Room cannot be used by 2 classes simultaneously)
                if G.nodes[other_matkul]['ruangan'] == ruangan_matkul:
                    return False # Bentrok ruangan pada waktu yang sama

    return True

    
# --- COLORING ALGORITHM (Standard Greedy) ---

def standard_greedy_coloring(G):
    """
    Performs a Greedy Graph Coloring with LEAST-USED Heuristic.
    Picks the safe slot that is currently LEAST occupied across all days
    to ensure the schedule is spread out (not stacked in the morning).
    """
    # Sort nodes by degree (Highest conflicts first)
    nodes_sorted = sorted(G.nodes(), key=lambda n: G.degree[n], reverse=True)
    
    coloring_result = {} 
    
    # Track usage of each slot to ensure spreading
    # Key: (day, start_time), Value: Number of courses scheduled in this slot
    slot_usage = {(day, time): 0 for day in DAYS for time in AVAILABLE_START_TIMES}

    for matkul in nodes_sorted:
        # Find ALL possible safe slots for this course
        candidate_slots = []
        
        for day in DAYS:
            for start_time in AVAILABLE_START_TIMES:
                if is_safe_to_place(G, matkul, day, start_time, coloring_result):
                    candidate_slots.append((day, start_time))
        
        if not candidate_slots:
            print(f"Warning: Could not schedule {matkul} (Constraint deadlock)")
            continue

        # Logic Fix: Least Used Strategy
        # Instead of taking the first available slot, pick the one with LOWEST usage count.
        # This forces the algorithm to fill empty afternoon slots before stacking mornings.
        best_slot = min(candidate_slots, key=lambda s: slot_usage[s])
        
        # Assign the best slot
        coloring_result[matkul] = best_slot
        
        # Mark this slot as 'busier'
        slot_usage[best_slot] += 1

    if len(coloring_result) != len(G.nodes):
        print(f"Warning: Only {len(coloring_result)} out of {len(G.nodes)} courses were scheduled!")

    return coloring_result


def calculate_daily_load(G, coloring_result):
    """Calculates the total SKS load per day based on the new coloring result."""

    daily_load = {day: 0 for day in DAYS}

    # coloring_result is: {course: (Day, Start_Time)}
    for matkul, (day, _) in coloring_result.items():
        sks = G.nodes[matkul]['sks']
        if day in daily_load:
            daily_load[day] += sks

    return daily_load


# --- ATOMIC OPTIMIZATION FUNCTIONS (MOVE and SWAP) ---

def is_safe_to_swap(G, matkul1, slot1_tuple, matkul2, slot2_tuple, current_coloring):
    """
    Checks if matkul1 (at slot1_tuple) and matkul2 (at slot2_tuple) can be safely swapped.
    slot_tuple = (Day, Start_Time)
    """

    # 1. Check Safety of Course 1 at Slot 2 (Exclude Course 2 from the schedule)
    temp_coloring_for_m1 = {k: v for k, v in current_coloring.items() if k != matkul2}
    if not is_safe_to_place(G, matkul1, slot2_tuple[0], slot2_tuple[1], temp_coloring_for_m1):
        return False

    # 2. Check Safety of Course 2 at Slot 1 (Exclude Course 1 from the schedule)
    temp_coloring_for_m2 = {k: v for k, v in current_coloring.items() if k != matkul1}
    if not is_safe_to_place(G, matkul2, slot1_tuple[0], slot1_tuple[1], temp_coloring_for_m2):
        return False

    return True


def try_move(G, coloring, daily_load, heavy_day, light_day, mean_sks, variance):
    """Tries the MOVE operation (move course to a new day/time slot) to improve balance."""

    optimized = False

    # Courses on the heavy day, sorted by highest SKS first
    matkul_on_heavy_day = sorted([
        m for m, (day, _) in coloring.items() if day == heavy_day
    ], key=lambda m: G.nodes[m]['sks'], reverse=True)

    for matkul_move in matkul_on_heavy_day:
        current_slot_tuple = coloring[matkul_move]
        sks_matkul = G.nodes[matkul_move]['sks']

        # Target slot: Light day + all possible start times
        for target_start_time in AVAILABLE_START_TIMES:
            target_day = light_day

            if is_safe_to_place(G, matkul_move, target_day, target_start_time, coloring):

                # Tentatively apply MOVE
                coloring[matkul_move] = (target_day, target_start_time)
                new_daily_load = calculate_daily_load(G, coloring)
                new_sks_values = list(new_daily_load.values())
                new_variance = sum((x - mean_sks) ** 2 for x in new_sks_values)

                if new_variance < variance:
                    # Success: Keep the MOVE
                    print(f"MOVE SUCCESS: {matkul_move} ({sks_matkul} SKS) moved from {current_slot_tuple} ({heavy_day}) to {(target_day, target_start_time)} ({light_day}). Var: {variance:.2f} -> {new_variance:.2f}")
                    optimized = True
                    return optimized, new_variance # Exit and restart main optimization loop
                else:
                    coloring[matkul_move] = current_slot_tuple # Revert if not better

    return optimized, variance


def try_swap(G, coloring, daily_load, heavy_day, light_day, mean_sks, variance):
    """Tries the SWAP operation (exchange two courses' slots) to improve balance."""

    optimized = False

    # Courses on the heavy day (highest SKS first)
    matkul_on_heavy_day = sorted([
        m for m, (day, _) in coloring.items() if day == heavy_day
    ], key=lambda m: G.nodes[m]['sks'], reverse=True)

    # Courses on the light day (lowest SKS first)
    matkul_on_light_day = sorted([
        m for m, (day, _) in coloring.items() if day == light_day
    ], key=lambda m: G.nodes[m]['sks'])

    for matkul_heavy in matkul_on_heavy_day:
        sks_heavy = G.nodes[matkul_heavy]['sks']
        slot_heavy_tuple = coloring[matkul_heavy] # (day, start_time)

        for matkul_light in matkul_on_light_day:
            sks_light = G.nodes[matkul_light]['sks']
            slot_light_tuple = coloring[matkul_light] # (day, start_time)

            # SWAP is only effective if SKS Heavy > SKS Light (to move heavy SKS away from heavy day)
            if sks_heavy <= sks_light:
                continue

            if is_safe_to_swap(G, matkul_heavy, slot_heavy_tuple, matkul_light, slot_light_tuple, coloring):

                # Tentatively apply SWAP
                coloring[matkul_heavy] = slot_light_tuple
                coloring[matkul_light] = slot_heavy_tuple

                new_daily_load = calculate_daily_load(G, coloring)
                new_sks_values = list(new_daily_load.values())
                new_variance = sum((x - mean_sks) ** 2 for x in new_sks_values)

                if new_variance < variance:
                    # Success: Keep the SWAP
                    print(f"SWAP SUCCESS: Swapped {matkul_heavy} ({sks_heavy} SKS, {heavy_day}) and {matkul_light} ({sks_light} SKS, {light_day}). Var: {variance:.2f} -> {new_variance:.2f}")
                    optimized = True
                    return optimized, new_variance # Exit and restart main optimization loop
                else:
                    # Revert the swap
                    coloring[matkul_heavy] = slot_heavy_tuple
                    coloring[matkul_light] = slot_light_tuple

    return optimized, variance


# --- MAIN EQUITABLE COLORING FUNCTION (Driver) ---

def equitable_coloring_optimized(G, initial_coloring, max_iter=100):
    """
    The main driver for Equitable Coloring optimization using MOVE and SWAP.
    Uses daily SKS load variance as the balance metric.
    """

    coloring = initial_coloring.copy()

    print("\n[EQUITABLE COLORING OPTIMIZATION LOG]")

    for iteration in range(max_iter):
        daily_load = calculate_daily_load(G, coloring)

        sks_values = list(daily_load.values())
        if not sks_values: break

        mean_sks = sum(sks_values) / len(sks_values)
        variance = sum((x - mean_sks) ** 2 for x in sks_values)

        # Identify the most unbalanced days
        heavy_day = max(daily_load, key=daily_load.get)
        light_day = min(daily_load, key=daily_load.get)

        # Stopping condition: Variance is low, or the difference between the heaviest and lightest day is small
        if variance < 1.0 or daily_load[heavy_day] - daily_load[light_day] <= 1:
            print(f"Iteration {iteration}: Balance achieved. Variance: {variance:.2f}. Optimization stopped.")
            break

        print(f"\n--- Iteration {iteration} ---")
        print(f"Initial Load: {daily_load}. Variance: {variance:.2f}")
        print(f"Target: Balance between {heavy_day} and {light_day}")

        # 1. Try MOVE (Prioritized)
        optimized, new_variance = try_move(G, coloring, daily_load, heavy_day, light_day, mean_sks, variance)

        if optimized:
            continue

        # 2. Try SWAP if MOVE failed
        print("   -> MOVE FAILED. Trying SWAP.")
        optimized, new_variance = try_swap(G, coloring, daily_load, heavy_day, light_day, mean_sks, variance)

        if optimized:
            continue

        # 3. Optimization failed in this iteration
        if not optimized:
            print(f"Iteration {iteration}: No operation (MOVE/SWAP) found that reduces variance ({variance:.2f}). Optimization stopped.")
            break

    final_daily_load = calculate_daily_load(G, coloring)

    print("\n[LOG FINISHED]")
    return coloring, final_daily_load