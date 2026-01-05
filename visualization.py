import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from config import (
    CONFIG, 
    AVAILABLE_START_TIMES, 
    get_duration_minutes, 
    get_end_time
)

# --- GLOBAL SETTINGS ---
matplotlib.use('Agg')

# --- CONFLICT NETWORK VISUALIZATION ---
def visualize_conflict_graph(graph, filename='conflict_graph.png'):
    pos = nx.spring_layout(graph, seed=42)
    plt.figure(figsize=(12, 8))
    plt.title("Course Conflict Network Structure")
    node_sizes = [graph.nodes[n].get('credits', 1) * 300 for n in graph.nodes()]
    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_color='skyblue', edgecolors='black', alpha=0.8)
    nx.draw_networkx_edges(graph, pos, edge_color='silver', alpha=0.5)
    nx.draw_networkx_labels(graph, pos, font_size=9)
    plt.axis('off')
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

# --- SCHEDULING COLOR MAP ---
def visualize_colored_graph(graph, coloring_result, filename='colored_graph.png'):
    pos = nx.spring_layout(graph, seed=42)
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_title("Final Scheduling Results (Graph Coloring)")
    all_slots = sorted(list(set((str(d), str(t)) for d, t in coloring_result.values())))
    slot_to_index = {slot: i for i, slot in enumerate(all_slots)}
    node_colors = [slot_to_index[(str(coloring_result[n][0]), str(coloring_result[n][1]))] for n in graph.nodes()]
    cmap = plt.colormaps.get_cmap('Spectral').resampled(len(all_slots))
    nx.draw_networkx(graph, pos, node_color=node_colors, cmap=cmap, node_size=400, with_labels=True, font_size=7, edge_color='gray', alpha=0.8, ax=ax)
    legend_elements = [Patch(facecolor=cmap(i / (len(all_slots) - 1) if len(all_slots) > 1 else 0), label=f"{slot[0]} ({slot[1]})") for i, slot in enumerate(all_slots)]
    ax.legend(handles=legend_elements, title='Time Slots', loc='upper left', bbox_to_anchor=(1, 1), fontsize=8)
    ax.axis('off')
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

# --- CREDIT LOAD ANALYSIS ---
def visualize_credits_load(daily_load, filename='credits_load.png'):
    days = CONFIG['DAYS']
    credit_counts = [daily_load.get(day, 0) for day in days]
    plt.figure(figsize=(10, 6))
    plt.bar(days, credit_counts, color='darkslateblue')
    avg_credits = sum(credit_counts) / len(days)
    plt.axhline(avg_credits, color='crimson', linestyle='--', label=f'Avg Load ({avg_credits:.2f})')
    plt.ylabel("Total Credit Hours (SKS)")
    plt.title("Daily Credit Load Distribution")
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

# --- UNIVERSITY MASTER TABLE ---
# Renders the full schedule including the final end-limit row to show class completion
def visualize_schedule_matrix(graph, coloring_result):
    days = CONFIG['DAYS']
    times = AVAILABLE_START_TIMES + [CONFIG['END_LIMIT']]
    grid = {d: {t: "" for t in times} for d in days}

    for course, (day, start) in coloring_result.items():
        credits = graph.nodes[course]['credits']
        end = get_end_time(start, get_duration_minutes(credits))
        label = f"{course} [{credits} SKS] ({start}-{end})"
        
        start_idx = AVAILABLE_START_TIMES.index(start)
        for i in range(credits):
            if start_idx + i < len(AVAILABLE_START_TIMES):
                current_slot = AVAILABLE_START_TIMES[start_idx + i]
                grid[day][current_slot] = label if i == 0 else f"   ^ (cont. {course})"
            if i == credits - 1:
                if grid[day][end] == "":
                    grid[day][end] = f"   [Finishes {course}]"

    col_w = 30
    time_w = 7
    total_w = time_w + (len(days) * (col_w + 3)) + 1
    sep = "=" * total_w

    print(f"\n{sep}\n{' UNIVERSITY MASTER SCHEDULE '.center(total_w, '=')}\n{sep}")
    header = f"{'Time':<{time_w}}" + "".join([f" | {d.ljust(col_w)}" for d in days])
    print(header + f"\n{'-' * total_w}")

    for t in times:
        row = f"{t:<{time_w}}"
        for d in days:
            content = grid[d][t]
            row += f" | {content.ljust(col_w)}"
        print(row)
    print("-" * total_w)

# --- STUDENT INDIVIDUAL REPORTS ---
# Generates personalized schedules with clear start, continuation, and finish markers
def visualize_student_schedules(student_data, coloring_result, graph):
    days = CONFIG['DAYS']
    times = AVAILABLE_START_TIMES + [CONFIG['END_LIMIT']]
    col_w, time_w = 30, 7
    total_w = time_w + (len(days) * (col_w + 3)) + 1

    print("\n" + "#" * 60 + f"\n{' INDIVIDUAL STUDENT REPORTS '.center(60, '#')}\n" + "#" * 60)

    for sid, courses in student_data.items():
        grid = {d: {t: "" for t in times} for d in days}
        for c in courses:
            if c in coloring_result:
                day, start = coloring_result[c]
                credits = graph.nodes[c]['credits']
                end = get_end_time(start, get_duration_minutes(credits))
                label = f"{c} ({start}-{end})"
                
                start_idx = AVAILABLE_START_TIMES.index(start)
                for i in range(credits):
                    if start_idx + i < len(AVAILABLE_START_TIMES):
                        current_slot = AVAILABLE_START_TIMES[start_idx + i]
                        grid[day][current_slot] = label if i == 0 else f"   ^ (cont. {c})"
                    if i == credits - 1:
                        if grid[day][end] == "":
                            grid[day][end] = f"   [Finishes {c}]"

        print(f"\n[ Student ID: {sid} ]\n{'-' * total_w}")
        header = f"{'Time':<{time_w}}" + "".join([f" | {d.ljust(col_w)}" for d in days])
        print(f"{header}\n{'-' * total_w}")

        for t in times:
            row = f"{t:<{time_w}}" + "".join([f" | {grid[d][t].ljust(col_w)}" for d in days])
            print(row)
        print("-" * total_w)