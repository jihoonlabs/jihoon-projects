import unittest
import inspect
import workflow_energy_probe
from workflow_energy_probe import consume_energy

class TestWorkflowEnergyProbe(unittest.TestCase):
    def test_case_1(self):
        self.assertEqual(consume_energy(10, 3), 7)
    
    def test_case_2(self):
        self.assertEqual(consume_energy(2, 5), 0)
    
    def test_case_3(self):
        self.assertEqual(consume_energy(0, 0), 0)
    
    def test_case_4(self):
        functions = [name for name, obj in inspect.getmembers(workflow_energy_probe, inspect.isfunction) if obj.__module__ == workflow_energy_probe.__name__]
        self.assertEqual(sorted(functions), ['consume_energy'])
