# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.manager import Manager
from chimera.core.site import Site


class TestRotator:
    """
    Test suite for rotator interface using FakeRotator implementation.
    Tests core functionality including position control and movement operations.
    """

    def setup_method(self):
        """Setup method called before each test."""
        self.manager = Manager(port=8001)  # Use different port to avoid conflicts

        # Add site configuration
        self.manager.add_class(
            Site,
            "lna",
            {
                "name": "UFSC",
                "latitude": "-27 36 13",
                "longitude": "-48 31 20",
                "altitude": "20",
            },
        )

        # Add FakeRotator
        from chimera.instruments.fakerotator import FakeRotator

        self.manager.add_class(FakeRotator, "fake")
        self.rotator = self.manager.get_proxy("/FakeRotator/0")

    def teardown_method(self):
        """Teardown method called after each test."""
        self.manager.shutdown()

    def test_get_position(self):
        """Test getting rotator position."""
        position = self.rotator.get_position()
        assert isinstance(position, (int, float))
        assert position == 0.0  # FakeRotator starts at 0

    def test_move_to(self):
        """Test moving rotator to absolute position."""
        target_angle = 90.0
        self.rotator.move_to(target_angle)

        # Check final position
        position = self.rotator.get_position()
        assert position == target_angle

    def test_move_by(self):
        """Test moving rotator by relative angle."""
        # Start at known position
        self.rotator.move_to(45.0)
        initial_position = self.rotator.get_position()

        # Move by relative amount
        relative_angle = 30.0
        self.rotator.move_by(relative_angle)

        # Check final position
        final_position = self.rotator.get_position()
        expected_position = initial_position + relative_angle
        assert final_position == expected_position

    def test_multiple_moves(self):
        """Test multiple sequential moves."""
        positions = [0.0, 90.0, 180.0, 270.0, 360.0]

        for target in positions:
            self.rotator.move_to(target)
            current = self.rotator.get_position()
            assert current == target

    def test_negative_angles(self):
        """Test handling of negative angles."""
        self.rotator.move_to(-90.0)
        position = self.rotator.get_position()
        assert position == -90.0

    def test_large_angles(self):
        """Test handling of angles greater than 360 degrees."""
        self.rotator.move_to(450.0)
        position = self.rotator.get_position()
        assert position == 450.0  # FakeRotator doesn't normalize angles

    def test_relative_movements(self):
        """Test various relative movement scenarios."""
        # Start at 0
        assert self.rotator.get_position() == 0.0

        # Move positive
        self.rotator.move_by(45.0)
        assert self.rotator.get_position() == 45.0

        # Move negative
        self.rotator.move_by(-15.0)
        assert self.rotator.get_position() == 30.0

        # Large relative move
        self.rotator.move_by(330.0)
        assert self.rotator.get_position() == 360.0

    def test_position_consistency(self):
        """Test that position readings are consistent."""
        test_angles = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]

        for angle in test_angles:
            self.rotator.move_to(angle)
            # Get position multiple times to ensure consistency
            pos1 = self.rotator.get_position()
            pos2 = self.rotator.get_position()
            pos3 = self.rotator.get_position()

            assert pos1 == pos2 == pos3 == angle
