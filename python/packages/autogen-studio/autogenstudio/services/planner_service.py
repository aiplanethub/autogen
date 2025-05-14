from ..database import DatabaseManager
from ..datamodel.planner import Planner


class PlannerService:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save(self, plan_id: int, config: dict) -> Planner:

        plan = Planner(title="Planner", id=plan_id, config=config)
        response = self.db.upsert(plan, return_json=False)
        if response.status:
            return response.data

        msg = response.message
        raise Exception(f"Failed to update plan: {msg}")

    def get_by_plan_id(self, plan_id: int) -> Planner:
        response = self.db.get(Planner, {"id": plan_id})
        if response.status and len(response.data) != 0:
            return response.data

        if len(response.data) == 0:
            return None

        msg = response.message
        raise Exception(f"Failed to fetch plan: {msg}")

    def get_by_agent_id(self, agent_id: int) -> Planner:
        response = self.db.get(Planner, {"agent_id": agent_id})
        if response.status and len(response.data) != 0:
            return response.data

        if len(response.data) == 0:
            return None

        msg = response.message
        raise Exception(f"Failed to fetch plan: {msg}")
