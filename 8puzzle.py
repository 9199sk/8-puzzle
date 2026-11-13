"""
8-Puzzle Solver - B.Tech Computer Science Mini Project
Technology: Python 3, Tkinter, A* Search, Manhattan Distance

Run:
    python 8puzzle.py

No third-party packages are required.
"""

import heapq
import random
import time
import tkinter as tk
from tkinter import messagebox

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
GOAL_POS = {value: divmod(index, 3) for index, value in enumerate(GOAL)}
BG = "#0b1220"
PANEL = "#111c30"
PANEL_LIGHT = "#1b2942"
TEXT = "#e5edf8"
MUTED = "#9aabc4"
ACCENT = "#60a5fa"
GREEN = "#34d399"
TILE = "#263a59"
TILE_HOVER = "#34527d"
EMPTY = "#101a2b"


def manhattan(state):
    """Sum of each numbered tile's distance from its goal position."""
    distance = 0
    for index, value in enumerate(state):
        if value == 0:
            continue
        row, col = divmod(index, 3)
        goal_row, goal_col = GOAL_POS[value]
        distance += abs(row - goal_row) + abs(col - goal_col)
    return distance


def get_neighbors(state):
    """Return all states reachable by moving one tile into the blank."""
    blank = state.index(0)
    row, col = divmod(blank, 3)
    neighbors = []

    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            other = nr * 3 + nc
            new_state = list(state)
            new_state[blank], new_state[other] = new_state[other], new_state[blank]
            neighbors.append(tuple(new_state))
    return neighbors


def a_star(start):
    """
    A* search:
    f(n) = g(n) + h(n)
    g(n): moves made so far
    h(n): Manhattan distance to the goal
    """
    frontier = []
    counter = 0
    heapq.heappush(frontier, (manhattan(start), 0, counter, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    explored = 0

    while frontier:
        _, current_cost, _, current = heapq.heappop(frontier)
        if current_cost != cost_so_far.get(current):
            continue

        explored += 1
        if current == GOAL:
            path = []
            node = current
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path, explored

        for neighbor in get_neighbors(current):
            new_cost = current_cost + 1
            if new_cost < cost_so_far.get(neighbor, float("inf")):
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                counter += 1
                priority = new_cost + manhattan(neighbor)
                heapq.heappush(frontier, (priority, new_cost, counter, neighbor))

    return None, explored


def make_solvable_board(steps=35):
    """Create a solvable board by making legal moves from the goal."""
    state = GOAL
    previous = None
    for _ in range(steps):
        choices = [s for s in get_neighbors(state) if s != previous]
        next_state = random.choice(choices)
        previous, state = state, next_state
    return state


class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Solver | Artificial Intelligence Mini Project")
        self.root.geometry("940x700")
        self.root.minsize(820, 640)
        self.root.configure(bg=BG)

        self.board = make_solvable_board()
        self.initial_board = self.board
        self.solution = []
        self.solution_index = 0
        self.explored_count = 0
        self.move_count = 0
        self.started_at = None
        self.elapsed_before_pause = 0
        self.timer_job = None
        self.animation_job = None
        self.solving = False
        self.tile_buttons = []

        self.build_ui()
        self.draw_board()
        self.update_stats()
        self.update_status("Ready. Move a tile or ask the A* algorithm to solve it.")
        self.start_timer()

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 12))

        tk.Label(
            header, text="8-PUZZLE SOLVER", bg=BG, fg=TEXT,
            font=("Segoe UI", 23, "bold")
        ).pack(anchor="w")
        tk.Label(
            header, text="An interactive demonstration of the A* search algorithm",
            bg=BG, fg=MUTED, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(3, 0))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=10)

        left = tk.Frame(body, bg=PANEL, padx=20, pady=20)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(body, bg=BG, width=265)
        right.pack(side="right", fill="y", padx=(18, 0))
        right.pack_propagate(False)

        board_title = tk.Frame(left, bg=PANEL)
        board_title.pack(fill="x", pady=(0, 14))
        tk.Label(
            board_title, text="PUZZLE BOARD", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")
        tk.Label(
            board_title, text="3 × 3", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(side="right")

        self.board_frame = tk.Frame(left, bg=PANEL)
        self.board_frame.pack(expand=True)

        for i in range(9):
            button = tk.Button(
                self.board_frame, text="", width=5, height=2,
                font=("Segoe UI", 25, "bold"),
                bg=TILE, fg=TEXT, activebackground=TILE_HOVER,
                activeforeground=TEXT, relief="flat", bd=0,
                cursor="hand2",
                command=lambda index=i: self.manual_move(index)
            )
            button.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")
            self.tile_buttons.append(button)

        for i in range(3):
            self.board_frame.grid_rowconfigure(i, weight=1, minsize=92)
            self.board_frame.grid_columnconfigure(i, weight=1, minsize=92)

        tk.Label(
            left, text="Click a tile next to the empty space to move it.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
        ).pack(pady=(15, 0))

        self.status_label = tk.Label(
            left, text="", bg=PANEL, fg=ACCENT,
            font=("Segoe UI", 10), wraplength=470, justify="center"
        )
        self.status_label.pack(pady=(12, 0))

        self.make_stat_card(right, "MOVES", "moves_value")
        self.make_stat_card(right, "TIME", "time_value")
        self.make_stat_card(right, "MANHATTAN DISTANCE", "distance_value")
        self.make_stat_card(right, "STATES EXPLORED", "explored_value")
        self.make_stat_card(right, "SOLUTION LENGTH", "solution_value")

        controls = tk.Frame(right, bg=BG)
        controls.pack(fill="x", pady=(8, 0))

        self.add_button(controls, "Solve automatically", self.auto_solve, ACCENT, "#071426")
        self.add_button(controls, "Next step", self.next_step, PANEL_LIGHT, TEXT)
        self.add_button(controls, "New random puzzle", self.new_game, GREEN, "#06251d")
        self.add_button(controls, "Reset puzzle", self.reset_puzzle, PANEL_LIGHT, TEXT)

        info = tk.Frame(right, bg=PANEL, padx=14, pady=13)
        info.pack(fill="x", pady=(16, 0))
        tk.Label(
            info, text="HOW IT WORKS", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")
        explanation = (
            "A* chooses the state with the lowest f(n) = g(n) + h(n).\n\n"
            "g(n): moves already made\n"
            "h(n): Manhattan distance\n\n"
            "The blank space is shown as an empty tile."
        )
        tk.Label(
            info, text=explanation, bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9), justify="left", wraplength=225
        ).pack(anchor="w", pady=(8, 0))

        footer = tk.Label(
            self.root, text="Python • Tkinter • A* Search • Manhattan Distance",
            bg=BG, fg="#71839f", font=("Segoe UI", 9)
        )
        footer.pack(pady=(0, 14))

    def make_stat_card(self, parent, label, attribute):
        card = tk.Frame(parent, bg=PANEL, padx=14, pady=10)
        card.pack(fill="x", pady=(0, 9))
        tk.Label(
            card, text=label, bg=PANEL, fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")
        value = tk.Label(
            card, text="0", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 18, "bold")
        )
        value.pack(anchor="w", pady=(2, 0))
        setattr(self, attribute, value)

    def add_button(self, parent, label, command, background, foreground):
        button = tk.Button(
            parent, text=label, command=command,
            bg=background, fg=foreground, activebackground=background,
            activeforeground=foreground, relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"), cursor="hand2",
            padx=10, pady=11
        )
        button.pack(fill="x", pady=4)
        return button

    def draw_board(self):
        for index, value in enumerate(self.board):
            button = self.tile_buttons[index]
            if value == 0:
                button.configure(
                    text="", bg=EMPTY, activebackground=EMPTY,
                    state="disabled", cursor="arrow"
                )
            else:
                button.configure(
                    text=str(value), bg=TILE, activebackground=TILE_HOVER,
                    state="normal", cursor="hand2"
                )

    def update_stats(self):
        self.moves_value.configure(text=str(self.move_count))
        self.distance_value.configure(text=str(manhattan(self.board)))
        self.explored_value.configure(text=str(self.explored_count))
        length = len(self.solution) - 1 if self.solution else 0
        self.solution_value.configure(text=str(length))

    def update_status(self, message, color=ACCENT):
        self.status_label.configure(text=message, fg=color)

    def start_timer(self):
        if self.started_at is None:
            self.started_at = time.time()
        self.tick_timer()

    def tick_timer(self):
        elapsed = self.elapsed_before_pause + (time.time() - self.started_at)
        minutes, seconds = divmod(int(elapsed), 60)
        self.time_value.configure(text=f"{minutes:02d}:{seconds:02d}")
        self.timer_job = self.root.after(500, self.tick_timer)

    def stop_timer(self):
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.started_at is not None:
            self.elapsed_before_pause += time.time() - self.started_at
            self.started_at = None

    def cancel_animation(self):
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        self.solving = False

    def manual_move(self, index):
        if self.solving:
            return
        if index not in [self.board.index(0) - 3, self.board.index(0) + 3,
                         self.board.index(0) - 1, self.board.index(0) + 1]:
            return

        blank = self.board.index(0)
        if abs(index // 3 - blank // 3) + abs(index % 3 - blank % 3) != 1:
            return

        new_board = list(self.board)
        new_board[blank], new_board[index] = new_board[index], new_board[blank]
        self.board = tuple(new_board)
        self.move_count += 1
        self.solution = []
        self.draw_board()
        self.update_stats()

        if self.board == GOAL:
            self.stop_timer()
            self.update_status("Excellent! You solved the puzzle.", GREEN)
            messagebox.showinfo("Puzzle solved", f"You solved the puzzle in {self.move_count} moves.")
        else:
            self.update_status("Valid move. Keep going!")

    def prepare_solution(self):
        self.stop_timer()
        self.update_status("A* is searching for the shortest solution...", ACCENT)
        self.root.update_idletasks()
        path, explored = a_star(self.board)
        self.explored_count = explored
        self.solution = path or []
        self.solution_index = 0
        self.update_stats()
        self.start_timer()

        if not path:
            self.update_status("No solution found for this board.", "#f87171")
            return False

        self.update_status(
            f"Solution found! {len(path) - 1} moves; {explored} states explored.",
            GREEN
        )
        return True

    def next_step(self):
        if self.solving:
            return
        if self.board == GOAL:
            self.update_status("The puzzle is already solved.", GREEN)
            return
        if not self.solution or self.solution[0] != self.board:
            if not self.prepare_solution():
                return
        if self.solution_index < len(self.solution) - 1:
            self.solution_index += 1
            self.board = self.solution[self.solution_index]
            self.move_count += 1
            self.draw_board()
            self.update_stats()
            if self.board == GOAL:
                self.stop_timer()
                self.update_status("Solved! A* reached the goal state.", GREEN)
            else:
                self.update_status(
                    f"Step {self.solution_index} of {len(self.solution) - 1}"
                )

    def auto_solve(self):
        if self.solving:
            return
        if self.board == GOAL:
            self.update_status("The puzzle is already solved.", GREEN)
            return
        if not self.solution or self.solution[0] != self.board:
            if not self.prepare_solution():
                return
        self.solving = True
        self.animate_solution()

    def animate_solution(self):
        if not self.solving:
            return
        if self.solution_index >= len(self.solution) - 1:
            self.solving = False
            self.stop_timer()
            self.update_status("Solved! A* reached the goal state.", GREEN)
            messagebox.showinfo(
                "Puzzle solved",
                f"Solution completed in {len(self.solution) - 1} moves."
            )
            return

        self.solution_index += 1
        self.board = self.solution[self.solution_index]
        self.move_count += 1
        self.draw_board()
        self.update_stats()
        self.update_status(
            f"Solving... step {self.solution_index} of {len(self.solution) - 1}"
        )
        self.animation_job = self.root.after(350, self.animate_solution)

    def new_game(self):
        self.cancel_animation()
        self.stop_timer()
        self.board = make_solvable_board(random.randint(25, 45))
        self.initial_board = self.board
        self.solution = []
        self.solution_index = 0
        self.explored_count = 0
        self.move_count = 0
        self.elapsed_before_pause = 0
        self.started_at = None
        self.start_timer()
        self.draw_board()
        self.update_stats()
        self.update_status("New solvable puzzle generated. Good luck!")

    def reset_puzzle(self):
        self.cancel_animation()
        self.stop_timer()
        self.board = self.initial_board
        self.solution = []
        self.solution_index = 0
        self.explored_count = 0
        self.move_count = 0
        self.elapsed_before_pause = 0
        self.started_at = None
        self.start_timer()
        self.draw_board()
        self.update_stats()
        self.update_status("Puzzle reset to its starting arrangement.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()
