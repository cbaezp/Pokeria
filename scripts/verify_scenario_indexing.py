"""Verification script for scenario catalog indexing and grading."""

from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import ActionEVItem
from app.domain.training.scenario_generator import catalog

catalog.initialize()
scenarios = catalog.list_all_scenarios()
print(f"Total indexed training scenarios: {len(scenarios)}")
preflop_s = catalog.filter_scenarios(street="preflop")
flop_s = catalog.filter_scenarios(street="flop")
turn_s = catalog.filter_scenarios(street="turn")
river_s = catalog.filter_scenarios(street="river")
print(f"Preflop: {len(preflop_s)}, Flop: {len(flop_s)}, Turn: {len(turn_s)}, River: {len(river_s)}")

engine = DecisionGradingEngine()
ref = [
    ActionEVItem(action="Check", amount=None, frequency=0.7, action_ev=10.0),
    ActionEVItem(action="Bet", amount=20.0, frequency=0.3, action_ev=9.8),
]
res = engine.evaluate_solver_decision("Check", None, ref)
print(f"Graded Check: {res.grade.value}, EV loss: {res.raw_ev_loss}")
assert res.grade.value == "STRONG"
assert res.raw_ev_loss == 0.0

res_bet = engine.evaluate_solver_decision("Bet", 20.0, ref)
print(f"Graded Bet: {res_bet.grade.value}, EV loss: {res_bet.raw_ev_loss}")
assert res_bet.grade.value == "STRONG"
print("SCENARIO CATALOG AND GRADING VERIFICATION: ALL OK!")
