from sqlmodel import Field
from pydantic import BaseModel

from .db import BaseDBModel


class PlannerConfigSaveData(BaseModel):
    plan_id: int
    config: dict


class Planner(BaseDBModel):

    agent_id: int = Field(default=None, foreign_key="agnet.id")

    title: str = Field(nullable=False)
    config: dict = Field(default={}, nullable=True)
