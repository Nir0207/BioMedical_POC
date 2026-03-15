from agentic_api.workflows.research_workflow import AgenticResearchWorkflow


class AgenticService:
    def __init__(self, workflow: AgenticResearchWorkflow) -> None:
        self.workflow = workflow

    async def run_research_query(self, user_query: str, top_k: int) -> dict:
        return await self.workflow.run(user_query=user_query, top_k=top_k)
