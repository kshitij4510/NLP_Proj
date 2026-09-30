"""Unit tests for workflow state machine transitions."""
import pytest
from app.agents.states import STAGE_TRANSITIONS, next_stage, WorkflowContext
from app.models.job import JobStage, JobStatus


def test_all_stages_have_transitions():
    """Every stage except COMPLETED must have a defined next stage."""
    for stage in JobStage:
        if stage != JobStage.COMPLETED:
            assert stage in STAGE_TRANSITIONS, f"{stage} missing from STAGE_TRANSITIONS"


def test_planning_leads_to_discovery():
    assert next_stage(JobStage.PLANNING) == JobStage.DISCOVERY


def test_completed_has_no_next():
    assert next_stage(JobStage.COMPLETED) is None


def test_full_chain_terminates():
    """Walk the full chain — must reach COMPLETED and stop."""
    current = JobStage.PLANNING
    visited = []
    while current is not None:
        assert current not in visited, f"Cycle detected at {current}"
        visited.append(current)
        current = next_stage(current)
    assert JobStage.COMPLETED in visited


def test_workflow_context_fail():
    ctx = WorkflowContext(project_id="proj-1", job_id="job-1")
    ctx.fail("something broke")
    assert ctx.status == JobStatus.FAILED
    assert ctx.error == "something broke"
    assert ctx.completed_at is not None


def test_workflow_context_complete():
    ctx = WorkflowContext(project_id="proj-1", job_id="job-1")
    ctx.complete()
    assert ctx.status == JobStatus.COMPLETED
    assert ctx.current_stage == JobStage.COMPLETED


def test_workflow_context_record_stage_output():
    ctx = WorkflowContext(project_id="proj-1", job_id="job-1")
    ctx.record_stage_output(JobStage.PLANNING, {"queries": ["q1"]})
    assert ctx.stage_outputs[JobStage.PLANNING.value] == {"queries": ["q1"]}
    assert ctx.current_stage == JobStage.PLANNING
