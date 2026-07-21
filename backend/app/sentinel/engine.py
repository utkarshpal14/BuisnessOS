from typing import List, Dict, Any
from app.agents.base_agent import Task
from app.agents.planner import PlannerAgent

class EnterpriseIntelligenceEngine:
    """
    Enterprise Intelligence Engine: Proactive KPI monitoring engine.
    Detects anomalies and generates Task(source="sentinel") for the PlannerAgent.
    """

    def __init__(self, planner: PlannerAgent):
        self.planner = planner

    def check_kpis(self) -> List[Task]:
        """
        Pull metrics, compare thresholds, create investigation tasks on breach.
        """
        tasks = []
        # Anomaly detection logic will go here
        return tasks

    def run_cycle(self):
        tasks = self.check_kpis()
        results = []
        for task in tasks:
            # Passes sentinel task through the same Planner Agent code path as reactive queries
            res = self.planner.handle(task, role="sentinel")
            results.append(res)
        return results
