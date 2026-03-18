"""Tests for Donormatch."""
from src.core import Donormatch
def test_init(): assert Donormatch().get_stats()["ops"] == 0
def test_op(): c = Donormatch(); c.process(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Donormatch(); [c.process() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Donormatch(); c.process(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Donormatch(); r = c.process(); assert r["service"] == "donormatch"
