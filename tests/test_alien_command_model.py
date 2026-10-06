#!/usr/bin/env python3
"""Boundary tests for the actual game-to-Laya packet, without loading weights."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import urllib.request
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("alien_model",ROOT/"scripts"/"alien-command-model.py")
model = importlib.util.module_from_spec(spec); spec.loader.exec_module(model)
class PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/"build"/"local"/"test-xcom1"/"xcom1"/"audit-fixture.sav.alien-command.jsonl"
        events=[json.loads(line) for line in path.read_text().splitlines()]
        cls.input=next(e["input"] for e in reversed(events) if e.get("input",{}).get("evidence"))
    def test_real_engine_packet_has_supported_choice_and_abstention(self):
        state, questions, mapping=model.build_packet(self.input)
        self.assertGreaterEqual(len(mapping),1)
        self.assertEqual(len(questions["recon"]["criteria"]),len(mapping)+1)
        self.assertIn("evidence_id",state)
        self.assertNotIn("base",state.lower())
    def test_empty_knowledge_cannot_create_a_region_choice(self):
        data=copy.deepcopy(self.input); data["beliefs"]=[]; data["evidence"]=[]
        self.assertEqual(model.build_packet(data)[2],{})
    def test_operations_have_distinct_capabilities(self):
        data=copy.deepcopy(self.input); region=data["beliefs"][0]["region"]
        data["candidates"]=[{"mission":m,"region":region} for m in ["STR_ALIEN_RESEARCH","STR_ALIEN_RETALIATION"]]
        _,questions,mapping=model.build_packet(data)
        text=" ".join(questions["recon"]["criteria"].values())
        self.assertIn("cannot discover bases",text)
        self.assertIn("discovery can trigger assault",text)
        self.assertEqual(len(mapping),2)
    def test_hidden_state_fields_are_rejected(self):
        data=copy.deepcopy(self.input); data["playerBases"]=[{"longitude":1}]
        with self.assertRaises(ValueError): model.build_packet(data)
    def test_unadmitted_report_is_rejected(self):
        data=copy.deepcopy(self.input); data["evidence"][0]["transmission"]="REPORTER_LOST"
        with self.assertRaises(ValueError): model.build_packet(data)
    def test_invented_evidence_is_rejected(self):
        data=copy.deepcopy(self.input); data["beliefs"][0]["evidenceIds"]=[99999]
        with self.assertRaises(ValueError): model.build_packet(data)
    def test_nonfinite_coordinates_are_rejected(self):
        data=copy.deepcopy(self.input); data["evidence"][0]["latitude"]=float("nan")
        with self.assertRaises(ValueError): model.build_packet(data)
    def test_out_of_menu_belief_does_not_create_an_option(self):
        data=copy.deepcopy(self.input); region=data["beliefs"][0]["region"]
        data["candidates"]=[c for c in data["candidates"] if c["region"]!=region]
        self.assertEqual(model.build_packet(data)[2],{})
    def test_duplicate_candidate_is_rejected(self):
        data=copy.deepcopy(self.input); data["candidates"].append(data["candidates"][0])
        with self.assertRaises(ValueError): model.build_packet(data)
    def test_candidate_order_does_not_change_model_packet(self):
        data=copy.deepcopy(self.input); data["candidates"].reverse()
        self.assertEqual(model.build_packet(data)[:2],model.build_packet(self.input)[:2])
if __name__=="__main__": unittest.main()
