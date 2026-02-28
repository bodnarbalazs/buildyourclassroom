"""Tests for ClassroomSimulation service."""
import numpy as np
import pytest

from services.classroom_simulation import ENGAGEMENT_TO_EMOTION, ClassroomSimulation


class TestInitialization:
    def test_grid_shape(self):
        sim = ClassroomSimulation(rows=5, cols=6, cycles=10, seed=42)
        assert sim._grid.shape == (5, 6)

    def test_engagement_within_bounds(self):
        sim = ClassroomSimulation(rows=5, cols=6, cycles=10, max_engagement=5, seed=42)
        assert sim._grid.min() >= 0
        assert sim._grid.max() <= 5

    def test_seed_produces_deterministic_grid(self):
        a = ClassroomSimulation(rows=3, cols=3, cycles=5, seed=99)
        b = ClassroomSimulation(rows=3, cols=3, cycles=5, seed=99)
        np.testing.assert_array_equal(a._grid, b._grid)


class TestRun:
    def test_returns_correct_number_of_ticks(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=10, seed=42)
        ticks = sim.run(schedule=[])
        # Initial state + 10 cycles = 11 ticks
        assert len(ticks) == 11

    def test_tick_zero_is_initial_state(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=5, seed=42)
        ticks = sim.run(schedule=[])
        assert ticks[0]["cycle"] == 0

    def test_last_tick_matches_cycles(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=7, seed=42)
        ticks = sim.run(schedule=[])
        assert ticks[-1]["cycle"] == 7

    def test_student_count_matches_grid(self):
        sim = ClassroomSimulation(rows=5, cols=6, cycles=5, seed=42)
        ticks = sim.run(schedule=[])
        for tick in ticks:
            assert len(tick["students"]) == 30

    def test_avg_engagement_is_plausible(self):
        sim = ClassroomSimulation(rows=5, cols=6, cycles=5, max_engagement=5, seed=42)
        ticks = sim.run(schedule=[])
        for tick in ticks:
            assert 0 <= tick["avg_engagement"] <= 5

    def test_student_emotions_are_valid(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=5, seed=42)
        ticks = sim.run(schedule=[])
        valid_emotions = set(ENGAGEMENT_TO_EMOTION.values())
        for tick in ticks:
            for s in tick["students"]:
                assert s["emotion"] in valid_emotions

    def test_student_ids_are_sequential(self):
        sim = ClassroomSimulation(rows=3, cols=4, cycles=3, seed=42)
        ticks = sim.run(schedule=[])
        for tick in ticks:
            ids = [s["id"] for s in tick["students"]]
            assert ids == list(range(12))

    def test_deterministic_with_same_seed(self):
        schedule = [{"time": 3, "action": 1}]
        a = ClassroomSimulation(rows=3, cols=3, cycles=10, seed=42)
        b = ClassroomSimulation(rows=3, cols=3, cycles=10, seed=42)
        assert a.run(schedule) == b.run(schedule)


class TestSchedule:
    def test_schedule_is_1_based(self):
        """time=1 in the schedule should apply at cycle 0 (first cycle)."""
        sim = ClassroomSimulation(rows=3, cols=3, cycles=5, max_engagement=5, seed=42)
        initial_grid = sim._grid.copy()
        # Action 5 (energizer) adds +1 to everyone
        ticks = sim.run(schedule=[{"time": 1, "action": 5}])
        # After the first cycle, at least some students should differ from pure baseline
        # (the energizer boosted them before fatigue/neighbor effects)
        assert ticks[1]["avg_engagement"] != ticks[0]["avg_engagement"]

    def test_schedule_with_duration(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=10, seed=42)
        ticks = sim.run(schedule=[{"time": 3, "action": 3, "duration": 5}])
        assert len(ticks) == 11


class TestTeacherActions:
    def test_action_5_boosts_everyone(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=1, max_engagement=5, seed=42)
        before = sim._grid.copy()
        sim._apply_action(5)
        expected = np.clip(before + 1, 0, 5)
        np.testing.assert_array_equal(sim._grid, expected)

    def test_action_1_boosts_low_engagement(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=1, max_engagement=5, seed=42)
        sim._grid = np.array([[0, 1, 2], [3, 4, 5], [2, 1, 0]])
        sim._apply_action(1)
        # Students with engagement <= 2 get +1
        assert sim._grid[0, 0] == 1
        assert sim._grid[0, 1] == 2
        assert sim._grid[0, 2] == 3
        # Students with engagement > 2 stay the same
        assert sim._grid[1, 0] == 3
        assert sim._grid[1, 1] == 4

    def test_action_6_sets_interactive_timer(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=1, max_engagement=5, seed=42)
        sim._apply_action(6, duration=4)
        assert sim._interactive_timer == 4

    def test_unknown_action_is_noop(self):
        sim = ClassroomSimulation(rows=3, cols=3, cycles=1, max_engagement=5, seed=42)
        before = sim._grid.copy()
        sim._apply_action(99)
        np.testing.assert_array_equal(sim._grid, before)


class TestEngagementToEmotion:
    @pytest.mark.parametrize("level,expected", [
        (5, "engaged"),
        (4, "engaged"),
        (3, "passive"),
        (2, "anxious"),
        (1, "confused"),
        (0, "disruptive"),
    ])
    def test_mapping(self, level, expected):
        assert ENGAGEMENT_TO_EMOTION[level] == expected
