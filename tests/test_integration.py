"""Integration tests for Donormatch."""
from src.core import Donormatch

class TestDonormatch:
    def setup_method(self):
        self.c = Donormatch()
    def test_10_ops(self):
        for i in range(10): self.c.process(i=i)
        assert self.c.get_stats()["ops"] == 10
    def test_service_name(self):
        assert self.c.process()["service"] == "donormatch"
    def test_different_inputs(self):
        self.c.process(type="a"); self.c.process(type="b")
        assert self.c.get_stats()["ops"] == 2
    def test_config(self):
        c = Donormatch(config={"debug": True})
        assert c.config["debug"] is True
    def test_empty_call(self):
        assert self.c.process()["ok"] is True
    def test_large_batch(self):
        for _ in range(100): self.c.process()
        assert self.c.get_stats()["ops"] == 100
