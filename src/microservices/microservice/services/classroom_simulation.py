from __future__ import annotations

import numpy as np
from scipy.signal import convolve2d

# Moore neighborhood kernel (8 surrounding cells)
_KERNEL = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])

ENGAGEMENT_TO_EMOTION = {
    5: "engaged",
    4: "engaged",
    3: "passive",
    2: "anxious",
    1: "confused",
    0: "disruptive",
}


class ClassroomSimulation:
    """Cellular automata simulation of student engagement in a classroom.

    Each cell in a 2D grid represents a student with an integer engagement
    level (0 to ``max_engagement``). Three forces evolve the grid each cycle:

    1. **Neighbor influence** — students drift toward their neighbors' average.
    2. **Time-based fatigue** — engagement decays quadratically over the lesson.
    3. **Teacher actions** — discrete interventions that boost or redirect engagement.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        cycles: int,
        max_engagement: int = 5,
        neighbor_strength: float = 0.7,
        base_fatigue: float = 0.01,
        fatigue_growth: float = 0.06,
        seed: int | None = None,
    ) -> None:
        self._rng = np.random.default_rng(seed)

        self.rows = rows
        self.cols = cols
        self.cycles = cycles
        self.max_engagement = max_engagement
        self.neighbor_strength = neighbor_strength
        self.base_fatigue = base_fatigue
        self.fatigue_growth = fatigue_growth

        self._grid = self._rng.integers(0, max_engagement + 1, size=(rows, cols))
        self._interactive_timer = 0

    def _baseline_update(self, t: int) -> None:
        neighbor_sum = convolve2d(self._grid, _KERNEL, mode="same", boundary="fill", fillvalue=0)
        neighbor_count = convolve2d(
            np.ones_like(self._grid), _KERNEL, mode="same", boundary="fill", fillvalue=0
        )
        neighbor_avg = neighbor_sum / neighbor_count

        new_grid = self._grid.copy()

        # Neighbor influence (doubled during interactive activities)
        multiplier = 2 if self._interactive_timer > 0 else 1
        k = self.neighbor_strength * multiplier
        diff = neighbor_avg - self._grid

        prob_increase = np.clip(k * (diff / self.max_engagement), 0, 1)
        prob_decrease = np.clip(k * (-diff / self.max_engagement), 0, 1)

        rand = self._rng.random((self.rows, self.cols))
        new_grid += (rand < prob_increase).astype(int)
        new_grid -= (rand < prob_decrease).astype(int)

        # Time-based fatigue (quadratic acceleration)
        fatigue_prob = self.base_fatigue + self.fatigue_growth * (t / self.cycles) ** 2
        fatigue_rand = self._rng.random((self.rows, self.cols))
        new_grid -= (fatigue_rand < fatigue_prob).astype(int)

        self._grid = np.clip(new_grid, 0, self.max_engagement).astype(int)

    def _apply_action(self, action: int, duration: int = 0) -> None:
        match action:
            case 1:  # Lecture question — boost low-engagement students
                boost = (self._grid <= 2).astype(int)
                self._grid = np.clip(self._grid + boost, 0, self.max_engagement)
            case 2:  # Targeted check — boost a random 2×2 region
                r = self._rng.integers(0, max(self.rows - 1, 1))
                c = self._rng.integers(0, max(self.cols - 1, 1))
                self._grid[r : r + 2, c : c + 2] += 2
                self._grid = np.clip(self._grid, 0, self.max_engagement)
            case 3:  # Group activity — double neighbor influence for N cycles
                self._interactive_timer = duration
            case 4:  # Individual support — help worst student, slight cost to others
                idx = np.unravel_index(np.argmin(self._grid), self._grid.shape)
                self._grid[idx] += 2
                self._grid -= 1
                self._grid[idx] += 1
                self._grid = np.clip(self._grid, 0, self.max_engagement)
            case 5:  # Energizer — boost everyone
                self._grid = np.clip(self._grid + 1, 0, self.max_engagement)
            case 6:  # Game challenge — boost everyone + interactive mode
                self._grid = np.clip(self._grid + 1, 0, self.max_engagement)
                self._interactive_timer = duration

    def _grid_to_students(self) -> list[dict]:
        flat = self._grid.flatten()
        return [
            {"id": int(i), "engagement": int(flat[i]), "emotion": ENGAGEMENT_TO_EMOTION[int(flat[i])]}
            for i in range(len(flat))
        ]

    def run(self, schedule: list[dict]) -> list[dict]:
        """Run the full simulation and return a list of tick snapshots.

        Args:
            schedule: List of ``{"time": int, "action": int, "duration"?: int}``
                      where ``time`` is 1-based (matching agenda start_minute).

        Returns:
            List of tick dicts, one per cycle (plus initial state at index 0).
            Each tick: ``{"cycle": int, "students": [...], "avg_engagement": float}``
        """
        # Convert 1-based schedule times to 0-based
        schedule_0 = [
            {**e, "time": int(e["time"]) - 1} for e in schedule
        ]

        ticks: list[dict] = []

        # Record initial state (cycle 0)
        ticks.append({
            "cycle": 0,
            "students": self._grid_to_students(),
            "avg_engagement": float(np.mean(self._grid)),
        })

        for t in range(self.cycles):
            # Apply scheduled teacher actions for this timestep
            for event in schedule_0:
                if event["time"] == t:
                    self._apply_action(int(event["action"]), int(event.get("duration", 0)))

            self._baseline_update(t)

            if self._interactive_timer > 0:
                self._interactive_timer -= 1

            ticks.append({
                "cycle": t + 1,
                "students": self._grid_to_students(),
                "avg_engagement": float(np.mean(self._grid)),
            })

        return ticks
