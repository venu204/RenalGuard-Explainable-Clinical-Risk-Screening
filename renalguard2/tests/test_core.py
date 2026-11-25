"""Unit tests — no DB or ML models needed."""
import sys, os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"]   = "test-secret-key-32-chars-minimum-x"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest


class TestRiskEngine:
    def test_low_all_zero(self):
        from app.clinical.engines import compute_icrri
        icrri, cat, _ = compute_icrri(0.0, 0.0, 0.0)
        assert icrri == 0.0 and cat == "LOW"

    def test_critical_all_one(self):
        from app.clinical.engines import compute_icrri
        icrri, cat, _ = compute_icrri(1.0, 1.0, 1.0)
        assert icrri == 100.0 and cat == "CRITICAL"

    def test_bounded_0_100(self):
        from app.clinical.engines import compute_icrri
        for ckd, dm, htn in [(0.9,0.9,0.9),(0.1,0.1,0.1),(0.5,0.5,0.5)]:
            icrri, _, _ = compute_icrri(ckd, dm, htn)
            assert 0.0 <= icrri <= 100.0

    def test_high_risk(self):
        from app.clinical.engines import compute_icrri
        _, cat, _ = compute_icrri(0.9, 0.7, 0.8)
        assert cat in ("HIGH", "CRITICAL")

    def test_moderate(self):
        from app.clinical.engines import compute_icrri
        icrri, cat, _ = compute_icrri(0.3, 0.3, 0.3)
        assert cat in ("LOW", "MODERATE")


class TestRuleEngine:
    def test_critical_potassium(self):
        from app.clinical.engines import evaluate_rules
        alerts = evaluate_rules({"potassium": 6.2})
        assert any(a["rule_id"] == "ELECTROLYTE_001" for a in alerts)
        assert any(a["severity"] == "CRITICAL" for a in alerts)

    def test_normal_no_alerts(self):
        from app.clinical.engines import evaluate_rules
        alerts = evaluate_rules({"potassium": 4.0, "creatinine": 1.0, "systolic_bp": 120})
        assert len(alerts) == 0

    def test_htn_crisis(self):
        from app.clinical.engines import evaluate_rules
        alerts = evaluate_rules({"systolic_bp": 190})
        assert any(a["rule_id"] == "HTN_002" for a in alerts)

    def test_missing_values_skipped(self):
        from app.clinical.engines import evaluate_rules
        assert evaluate_rules({}) == []

    def test_sorted_by_severity(self):
        from app.clinical.engines import evaluate_rules
        alerts = evaluate_rules({"potassium": 6.5, "systolic_bp": 145, "creatinine": 2.0})
        order = {"CRITICAL":0,"HIGH":1,"MODERATE":2,"LOW":3,"INFORMATIONAL":4}
        for i in range(len(alerts)-1):
            assert order[alerts[i]["severity"]] <= order[alerts[i+1]["severity"]]

    def test_severe_anaemia(self):
        from app.clinical.engines import evaluate_rules
        alerts = evaluate_rules({"hemoglobin": 6.5})
        assert any(a["rule_id"] == "ANAEMIA_002" for a in alerts)

    def test_diabetes_alert(self):
        from app.clinical.engines import evaluate_rules
        alerts = evaluate_rules({"hba1c": 9.0})
        assert any(a["rule_id"] == "DIABETES_002" for a in alerts)


class TestSecurity:
    def test_hash_verify(self):
        from app.core.security import hash_password, verify_password
        h = hash_password("MyPass@123")
        assert verify_password("MyPass@123", h)
        assert not verify_password("Wrong", h)

    def test_jwt_roundtrip(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token({"sub": "42", "role": "DOCTOR"})
        payload = decode_token(token)
        assert payload and payload["sub"] == "42"

    def test_invalid_token_none(self):
        from app.core.security import decode_token
        assert decode_token("not.a.real.token") is None

    def test_tampered_token_none(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token({"sub": "1"})
        assert decode_token(token[:-4] + "XXXX") is None


class TestTrend:
    def _t(self, vals):
        from app.services.services import _trend
        return _trend(vals)

    def test_improving(self):   assert self._t([70, 65, 58]) == "IMPROVING"
    def test_worsening(self):   assert self._t([40, 50, 62]) == "WORSENING"
    def test_stable(self):      assert self._t([50, 51, 50]) == "STABLE"
    def test_empty(self):       assert self._t([]) is None
    def test_single(self):      assert self._t([55]) is None
