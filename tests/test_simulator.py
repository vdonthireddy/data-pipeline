import unittest
from simulator.main import get_sensor_value

class TestSensorSimulator(unittest.TestCase):
    def test_temperature_range(self):
        val = get_sensor_value("temperature")
        self.assertTrue(20.0 <= val <= 110.0)

    def test_pressure_range(self):
        val = get_sensor_value("pressure")
        self.assertTrue(90.0 <= val <= 160.0)

    def test_invalid_sensor(self):
        val = get_sensor_value("unknown")
        self.assertEqual(val, 0.0)

if __name__ == '__main__':
    unittest.main()
