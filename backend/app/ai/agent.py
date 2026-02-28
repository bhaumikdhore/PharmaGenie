from app.ai.llm import llm
from app.ai.tools.medicine_tool import search_medicine

try:
    # LangChain pre-1.0 agent API
    from langchain.agents import initialize_agent, AgentType
except Exception:
    initialize_agent = None
    AgentType = None


class AppAgent:
    def __init__(self) -> None:
        self.tools = [search_medicine]
        self.llm = llm
        self._legacy_agent = None

        if initialize_agent and AgentType:
            self._legacy_agent = initialize_agent(
                self.tools,
                self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
            )

    def _extract_medicine_name(self, query: str) -> str:
        cleaned = query.strip().rstrip("?.!")
        lowered = cleaned.lower()

        for marker in ("do you have", "have", "search", "find", "medicine", "for"):
            idx = lowered.rfind(marker)
            if idx != -1:
                candidate = cleaned[idx + len(marker):].strip(" :,-")
                if candidate:
                    return candidate

        return cleaned

    async def arun(self, query: str, callbacks=None):
        if self._legacy_agent is not None:
            try:
                return await self._legacy_agent.arun(query, callbacks=callbacks)
            except TypeError:
                return await self._legacy_agent.arun(query)

        medicine_name = self._extract_medicine_name(query)

        try:
            tool_result = await search_medicine.ainvoke({"name": medicine_name})
        except Exception:
            return "I couldn't query the medicine database right now. Please check database connectivity and try again."

        prompt = (
            "You are a pharmacy assistant. "
            "Answer the user query using only the provided database tool result. "
            "If not found, clearly say it is not available.\n\n"
            f"User query: {query}\n"
            f"Tool result: {tool_result}\n\n"
            "Give a short, helpful response."
        )

        try:
            if callbacks:
                response = await self.llm.ainvoke(prompt, config={"callbacks": callbacks})
            else:
                response = await self.llm.ainvoke(prompt)
            if hasattr(response, "content") and response.content:
                return response.content
            return str(response)
        except Exception:
            return str(tool_result)


agent = AppAgent()
