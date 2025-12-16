import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
from datetime import datetime, timedelta

# Use the 'Agg' backend for non-interactive environments (like servers)
matplotlib.use('Agg')

# --- TIME HELPER FUNCTIONS (Redefine or import from graph_core) ---
# Redefined here to keep the visualization module self-contained and less reliant on graph_core's internal structure.

def get_duration_minutes(sks):
    """Converts SKS (credit hours) to total duration in minutes (1 SKS = 50 minutes)."""
    return sks * 50

def get_end_time(start_time_str, duration_minutes):
    """Calculates the end time from a start time string and a given duration."""
    dummy_date = datetime.strptime(start_time_str, '%H:%M')
    end_time = dummy_date + timedelta(minutes=duration_minutes)
    return end_time.strftime('%H:%M')

# --- GRAPH VISUALIZATION ---

def visualize_conflict_graph(G, filename='conflict_graph.png'):
    """Visualizes the structure of graph G (nodes = courses, edges = conflicts)."""
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10, 7))
    plt.title("Scheduling Conflict Graph Structure")

    # Node size based on SKS (larger SKS means larger node)
    node_sizes = [d.get('sks', 1) * 200 for n, d in G.nodes(data=True)]
    
    nx.draw_networkx_nodes(G,
                        pos,
                        node_size=node_sizes,
                        node_color='lightblue',
                        edgecolors='black',
                        alpha=0.8)
    nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.6)

    node_labels = {node: node for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10)

    plt.axis('off')
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Conflict graph saved to: {filename}")


def visualize_colored_graph(G,
                            coloring_result,
                            filename='colored_graph.png'):
    """Visualizes the graph after coloring (scheduling)."""
    pos = nx.spring_layout(G, seed=42)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_title("Scheduling Result (Graph Coloring)")

    # The unique 'colors' are now tuples (Day, Start_Time)
    # Handle nodes that failed to be scheduled
    UNSCHEDULED_COLOR = ('UNSCHEDULED', '00:00')

    # Get all unique colors, including UNSCHEDULED if needed
    all_colors = set(coloring_result.values())
    if len(G.nodes()) != len(coloring_result):
        all_colors.add(UNSCHEDULED_COLOR)

    unique_colors = sorted(list(all_colors))
    color_map = {color: i for i, color in enumerate(unique_colors)}
    
    # Assign color index to each node
    node_colors = [
        color_map[coloring_result.get(node, UNSCHEDULED_COLOR)]
        for node in G.nodes()
    ]

    cmap = plt.colormaps.get_cmap('Spectral').resampled(len(unique_colors))

    nx.draw_networkx(G,
                    pos,
                    node_color=node_colors,
                    cmap=cmap,
                    node_size=300,
                    with_labels=True,
                    font_size=8,
                    edge_color='gray',
                    alpha=0.8,
                    ax=ax)

    # Create legend labels (Day, Start_Time)
    legend_elements = [
        Patch(facecolor=cmap(i / (len(unique_colors) - 1) if len(unique_colors) > 1 else 0),
            label=f"{day} ({start_time})"
            if day != 'UNSCHEDULED' else "Failed to Schedule")
        for i, (day, start_time) in enumerate(unique_colors)
    ]
    ax.legend(handles=legend_elements,
            title='Time Slot (Day, Start)',
            loc='upper left',
            fontsize=8)

    ax.axis('off')
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Colored graph saved to: {filename}")


def visualize_sks_load(daily_load, filename='sks_load.png'):
    """Visualizes the total SKS load per day."""
    days = list(daily_load.keys())
    sks_counts = list(daily_load.values())

    plt.figure(figsize=(8, 5))
    plt.bar(days, sks_counts, color='teal')

    average_sks = sum(sks_counts) / len(sks_counts)

    plt.axhline(average_sks,
                color='red',
                linestyle='--',
                label=f'Average SKS ({average_sks:.2f})')

    plt.xlabel("Day")
    plt.ylabel("Total SKS")
    plt.title("Daily SKS Load Balancing (Equitable Coloring Result)")
    plt.legend()
    plt.grid(axis='y', linestyle='--')
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"SKS load chart saved to: {filename}")


# --- MATRIX SCHEDULE VISUALIZATION ---


def visualize_schedule_matrix(G, coloring_result, relevant_days=None):
    """
    Visualizes the coloring result as an ASCII schedule table (Day vs Start Time).
    Handles multi-line cells for multiple courses in the same slot.
    """

    # --- DATA PRE-PROCESSING ---
    # Helper functions must be available locally or imported
    def get_duration_minutes(sks):
        return sks * 50

    def get_end_time(start_time, duration):
        try:
            start_dt = datetime.strptime(start_time, '%H:%M')
            end_dt = start_dt + timedelta(minutes=duration)
            return end_dt.strftime('%H:%M')
        except ValueError:
            return "??:??"

    if relevant_days is None:
        relevant_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Get all unique start times, sorted
    all_start_times = sorted(
        list(set(start for day, start in coloring_result.values())))

    # Data structure: {Day: {Start_Time: [Course Info...]}}
    cell_data = {
        day: {start: []
              for start in all_start_times}
        for day in relevant_days
    }

    for course, (day, start_time) in coloring_result.items():
        if day in relevant_days:
            sks = G.nodes[course]['sks']
            duration = get_duration_minutes(sks)
            end_time = get_end_time(start_time, duration)

            # Info to be placed in the cell
            info = f"{course} ({sks} SKS, {start_time}-{end_time})"
            cell_data[day][start_time].append(info)

    # 2. COLUMN WIDTH CALCULATION

    max_time_width = 5  # 'HH:MM'
    min_content_width = 30  # Minimum width for course content

    # Calculate max column width for each day
    col_widths = {day: len(day) for day in relevant_days}
    for day in relevant_days:
        max_content_len = len(day)
        for start_time in all_start_times:
            if cell_data[day][start_time]:
                max_content_len = max(
                    max_content_len, max(len(item) for item in cell_data[day][start_time]))

        col_widths[day] = max(max_content_len, min_content_width)

    # Total line width calculation
    total_width = max_time_width + sum(col_widths.values()) + (len(relevant_days) * 3) + 4

    # 3. PRINTING THE ASCII TABLE

    # Header
    print("\n" + "=" * total_width)
    print(f" CLASS MATRIX SCHEDULE (DAY VS START TIME) ".center(total_width, '='))
    print("=" * total_width)

    # Day Names Row
    header_line = f"{'Time':<{max_time_width}}"
    for day in relevant_days:
        header_line += f" | {day.ljust(col_widths[day])}"
    print(header_line)
    print("-" * total_width)

    # Content Rows (Iterate over Start Times)
    for start_time in all_start_times:

        # Find Max Row Height (Most courses in this time slot)
        max_height = 0
        row_content = {}
        for day in relevant_days:
            content = cell_data[day][start_time]
            row_content[day] = content
            max_height = max(max_height, len(content))

        # Print rows vertically (Handling Multi-Line Cells)
        for i in range(max_height):
            line = ""
            # Print Start Time only on the first line
            if i == 0:
                line += f"{start_time.ljust(max_time_width)}"
            else:
                line += f"{' '.ljust(max_time_width)}"

            for day in relevant_days:
                # Get the i-th course from that day (or an empty string)
                course_info = row_content[day][i] if i < len(
                    row_content[day]) else ""

                line += f" | {course_info.ljust(col_widths[day])}"

            print(line)

        print("-" * total_width)

    print("=" * total_width + "\n")
    return


# --- INDIVIDUAL STUDENT SCHEDULE VISUALIZATION ---

def visualize_student_schedule(data_mahasiswa, coloring_result, G):
    """
    Creates and displays a summarized schedule per student
    using a custom ASCII table format (Day, Start Time - End Time).
    """

    # Helper functions must be available
    def get_duration_minutes(sks):
        return sks * 50

    def get_end_time(start_time, duration):
        try:
            start_dt = datetime.strptime(start_time, '%H:%M')
            end_dt = start_dt + timedelta(minutes=duration)
            return end_dt.strftime('%H:%M')
        except ValueError:
            return "??:??"

    print("\n" + "=" * 80)
    print(
        " INDIVIDUAL STUDENT CLASS SCHEDULE ".center(80, '=')
    )
    print("=" * 80)

    # Get all unique used start times and days
    all_start_times = sorted(
        list(set(start for day, start in coloring_result.values())))
    all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Determine maximum column width across all student schedules
    MIN_COL_WIDTH = 25

    # Calculating the total line width
    max_time_width = 5
    total_width = max_time_width + len(all_days) * (MIN_COL_WIDTH + 3) + 4

    for mhs_id, matkul_set in data_mahasiswa.items():

        # 1. DATA PRE-PROCESSING FOR THIS STUDENT
        cell_data = {
            day: {start: [] for start in all_start_times}
            for day in all_days
        }

        for course in matkul_set:
            if course in coloring_result:
                day, start_time = coloring_result[course]
                if day in all_days and start_time in all_start_times:
                    sks = G.nodes[course]['sks']
                    duration = get_duration_minutes(sks)
                    end_time = get_end_time(start_time, duration)

                    # Store course info in the cell
                    info = f"{course} ({sks} SKS, {start_time}-{end_time})"
                    cell_data[day][start_time].append(info)

        # 2. PRINTING THE ASCII STUDENT TABLE
        print(f"\n--- Student ID: {mhs_id} ---")

        # Day Names Row
        header_line = f"{'Time':<{max_time_width}}"
        for day in all_days:
            header_line += f" | {day.ljust(MIN_COL_WIDTH)}"

        print("-" * total_width)
        print(header_line)
        print("-" * total_width)

        # Content Rows (Iterate over Start Times)
        for start_time in all_start_times:

            # Find Max Row Height
            max_height = 0
            row_content = {}
            for day in all_days:
                content = cell_data[day][start_time]
                row_content[day] = content
                max_height = max(max_height, len(content))

            # Print rows vertically (Handling Multi-Line Cells)
            for i in range(max_height):
                line = ""
                # Print Start Time only on the first line
                if i == 0:
                    line += f"{start_time.ljust(max_time_width)}"
                else:
                    line += f"{' '.ljust(max_time_width)}"

                for day in all_days:
                    # Get the i-th course (or empty string)
                    course_info = row_content[day][i] if i < len(row_content[day]) else ""

                    # Use ljust() to ensure consistent width
                    line += f" | {course_info.ljust(MIN_COL_WIDTH)}"

                print(line)

            # Print separator line if there was content in this time slot
            if max_height > 0:
                print("-" * total_width)

    print("=" * 80 + "\n")
    return