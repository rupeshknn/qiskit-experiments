# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests for BackendTiming."""

from test.base import QiskitExperimentsTestCase

from ddt import data, ddt, unpack
from qiskit import QiskitError
from qiskit.providers.fake_provider import FakeNairobiV2

from qiskit_experiments.framework import BackendTiming


@ddt
class TestBackendTiming(QiskitExperimentsTestCase):
    """Test BackendTiming"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Creating a complete fake backend is difficult so we use one from
        # qiskit. Just to be safe, we check that the properties we care about
        # for these tests are never changed from what the tests assume.
        backend = FakeNairobiV2()
        target = backend.target
        assumptions = (
            (abs(target.dt * 4.5e9 - 1) < 1e-6)
            and target.acquire_alignment == 16
            and target.pulse_alignment == 1
            and target.min_length == 64
            and target.granularity == 16
        )
        if not assumptions:  # pragma: no cover
            raise ValueError("FakeNairobiV2 properties have changed!")

        cls.acquire_alignment = target.acquire_alignment
        cls.dt = target.dt
        cls.granularity = target.granularity
        cls.min_length = target.min_length
        cls.pulse_alignment = target.pulse_alignment

    @data((True, "s"), (False, "dt"))
    @unpack
    def test_delay_unit(self, null_dt, result):
        """Test delay unit matches dt"""
        backend = FakeNairobiV2()
        if null_dt:
            backend.target.dt = None
        timing = BackendTiming(backend)
        self.assertEqual(timing.delay_unit, result)

    def test_round_delay_args(self):
        """Test argument checking in round_delay"""
        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        with self.assertRaises(QiskitError):
            timing.round_delay(time=self.dt * 16, samples=16)
        with self.assertRaises(QiskitError):
            timing.round_delay()

    def test_round_pulse_args(self):
        """Test argument checking in round_pulse"""
        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        with self.assertRaises(QiskitError):
            timing.round_pulse(time=self.dt * 64, samples=64)
        with self.assertRaises(QiskitError):
            timing.round_pulse()

    @data([14, 16], [16, 16], [18, 16], [64.5, 64])
    @unpack
    def test_round_delay(self, samples_in, samples_out):
        """Test delay calculation with time input"""
        time = self.dt * samples_in

        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertEqual(timing.round_delay(time=time), samples_out)

    def test_round_delay_no_dt(self):
        """Test delay when dt is None"""
        time = self.dt * 16

        backend = FakeNairobiV2()
        backend.target.dt = None
        timing = BackendTiming(backend)
        self.assertEqual(timing.round_delay(time=time), time)

    @data([14, 16], [16, 16], [18, 16], [64.5, 64])
    @unpack
    def test_round_delay_samples_in(self, samples_in, samples_out):
        """Test delay calculation with samples input"""
        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertEqual(timing.round_delay(samples=samples_in), samples_out)

    @data([12, 64], [65, 64], [79, 80], [83, 80])
    @unpack
    def test_round_pulse(self, samples_in, samples_out):
        """Test round pulse calculation with time input"""
        time = self.dt * samples_in

        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertEqual(timing.round_pulse(time=time), samples_out)

    @data([12, 64], [65, 64], [79, 80], [83, 80], [80.5, 80])
    @unpack
    def test_round_pulse_samples_in(self, samples_in, samples_out):
        """Test round pulse calculation with samples input"""
        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertEqual(timing.round_pulse(samples=samples_in), samples_out)

    def test_delay_time(self):
        """Test delay_time calculation"""
        time_in = self.dt * 16.1
        time_out = self.dt * 16

        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertAlmostEqual(timing.delay_time(time=time_in), time_out, delta=1e-6 * self.dt)

    def test_delay_time_samples_in(self):
        """Test delay_time calculation"""
        samples_in = 16.1
        time_out = self.dt * 16

        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertAlmostEqual(
            timing.delay_time(samples=samples_in), time_out, delta=1e-6 * self.dt
        )

    def test_delay_time_no_dt(self):
        """Test delay time calculation when dt is None"""
        time_in = self.dt * 16.1
        time_out = time_in

        backend = FakeNairobiV2()
        backend.target.dt = None
        timing = BackendTiming(backend)
        self.assertAlmostEqual(timing.delay_time(time=time_in), time_out, delta=1e-6 * self.dt)

    def test_pulse_time(self):
        """Test pulse_time calculation"""
        time_in = self.dt * 85.1
        time_out = self.dt * 80

        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertAlmostEqual(timing.pulse_time(time=time_in), time_out, delta=1e-6 * self.dt)

    def test_pulse_time_samples_in(self):
        """Test pulse_time calculation"""
        samples_in = 85.1
        time_out = self.dt * 80

        backend = FakeNairobiV2()
        timing = BackendTiming(backend)
        self.assertAlmostEqual(
            timing.pulse_time(samples=samples_in), time_out, delta=1e-6 * self.dt
        )

    def test_round_pulse_no_dt_error(self):
        """Test methods that don't work when dt is None raise exceptions"""
        backend = FakeNairobiV2()
        backend.target.dt = None
        timing = BackendTiming(backend)

        time = self.dt * 81

        with self.assertRaises(QiskitError):
            timing.round_pulse(time=time)

    def test_unexpected_pulse_alignment(self):
        """Test that a weird pulse_alignment parameter is caught"""
        backend = FakeNairobiV2()
        backend.target.pulse_alignment = 33
        timing = BackendTiming(backend)
        with self.assertRaises(QiskitError):
            timing.round_pulse(samples=81)

    def test_unexpected_acquire_alignment(self):
        """Test that a weird acquire_alignment parameter is caught"""
        backend = FakeNairobiV2()
        try:
            backend.target.acquire_alignment = 33
        except AttributeError:
            backend.target.aquire_alignment = 33
        timing = BackendTiming(backend)
        with self.assertRaises(QiskitError):
            timing.round_pulse(samples=81)
