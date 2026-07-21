import logging
import time
from typing import Optional, List
from app.planner.models import PlannerTask, PlannerResponse, AgentResult
from app.planner.registry import AgentRegistry
from app.planner.router import TaskRouter, SimpleTaskRouter
from app.planner.exceptions import (
    PlannerException,
    AgentNotFoundException,
    UnknownTaskTypeException,
    InvalidTaskException,
)

logger = logging.getLogger("planner")

class PlannerService:
    """
    Core Planner Orchestration Service.
    Coordinates task routing, agent invocation, error handling, and response aggregation.
    Completely independent of FastAPI or web frameworks.
    """

    def __init__(self, registry: AgentRegistry, router: Optional[TaskRouter] = None):
        self.registry = registry
        self.router = router or SimpleTaskRouter()

    def validate_task(self, task: PlannerTask) -> None:
        """Validates that a task has required fields and non-empty query."""
        if not isinstance(task, PlannerTask):
            raise InvalidTaskException("Input must be a valid PlannerTask instance.")
        if not task.query or not task.query.strip():
            raise InvalidTaskException("Query content cannot be empty.")
        if not task.task_type or not task.task_type.strip():
            raise InvalidTaskException("Task type cannot be empty.")

    def execute_task(self, task: PlannerTask) -> PlannerResponse:
        """
        Executes a task end-to-end through task routing, agent execution, and response merging.
        Guaranteed not to crash on handled domain exceptions or agent errors.
        """
        start_time = time.perf_counter()
        errors: List[str] = []
        participating_agents: List[str] = []
        raw_results: List[dict] = []
        summaries: List[str] = []

        logger.info(f"Planner started: task_id={task.task_id}, type={task.task_type}, source={task.source}")

        # Input Validation
        try:
            self.validate_task(task)
        except InvalidTaskException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Planner failed: task_id={task.task_id}, error={str(e)}")
            return PlannerResponse(
                task_id=getattr(task, "task_id", "unknown"),
                status="failed",
                participating_agents=[],
                summary="Task validation failed.",
                raw_results=[],
                execution_time_ms=elapsed_ms,
                errors=[str(e)]
            )

        # Routing
        try:
            target_agent_names = self.router.route(task)
        except UnknownTaskTypeException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Planner failed: task_id={task.task_id}, error={str(e)}")
            return PlannerResponse(
                task_id=task.task_id,
                status="failed",
                participating_agents=[],
                summary="Routing failed: Unknown task type.",
                raw_results=[],
                execution_time_ms=elapsed_ms,
                errors=[str(e)]
            )

        # Agent Invocation
        successful_agent_count = 0
        for agent_name in target_agent_names:
            try:
                agent = self.registry.get(agent_name)
                logger.info(f"Agent invoked: task_id={task.task_id}, agent={agent_name}")
                participating_agents.append(agent_name)
                
                result = agent.execute(task)
                
                if result.status == "success":
                    successful_agent_count += 1
                    logger.info(f"Agent completed: task_id={task.task_id}, agent={agent_name}, status=success")
                else:
                    logger.warning(f"Agent completed with error: task_id={task.task_id}, agent={agent_name}")
                    if result.error_message:
                        errors.append(f"Agent '{agent_name}' error: {result.error_message}")
                
                if result.summary:
                    summaries.append(result.summary)
                
                raw_results.append(result.model_dump() if hasattr(result, "model_dump") else result.dict())

            except AgentNotFoundException as e:
                logger.error(f"Agent invocation failed: task_id={task.task_id}, agent={agent_name}, error={str(e)}")
                errors.append(str(e))
            except Exception as e:
                logger.error(f"Agent execution exception: task_id={task.task_id}, agent={agent_name}, error={str(e)}")
                errors.append(f"Unhandled exception in agent '{agent_name}': {str(e)}")

        # Response Aggregation & Status Determination
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        total_target_agents = len(target_agent_names)
        if successful_agent_count == total_target_agents and total_target_agents > 0:
            overall_status = "success"
        elif successful_agent_count > 0:
            overall_status = "partial_success"
        else:
            overall_status = "failed"

        merged_summary = " | ".join(summaries) if summaries else "No agent summaries available."

        if overall_status == "failed":
            logger.error(f"Planner failed: task_id={task.task_id}, status={overall_status}, errors={errors}")
        else:
            logger.info(f"Planner finished: task_id={task.task_id}, status={overall_status}, execution_time_ms={elapsed_ms:.2f}")

        return PlannerResponse(
            task_id=task.task_id,
            status=overall_status,
            participating_agents=participating_agents,
            summary=merged_summary,
            raw_results=raw_results,
            execution_time_ms=elapsed_ms,
            errors=errors
        )
