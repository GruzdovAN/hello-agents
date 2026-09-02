"""Официальный тест интеграции класса HelloAgents."""

from hello_agents import Config, SimpleAgent

from src.agents import build_agent_team
from src.config import LLMSettings
from src.tools import create_tool_registry


def test_build_agent_team_creates_four_official_simple_agents() -> None:
    settings = LLMSettings(
        model="test-model",
        api_key="test-secret-key",
        base_url="https://example.test/v1",
    )
    registry = create_tool_registry()

    team = build_agent_team(settings, registry)

    assert all(
        isinstance(agent, SimpleAgent)
        for agent in (team.analyst, team.architect, team.reviewer, team.synthesizer)
    )
    assert team.analyst.tool_registry is registry
    assert team.synthesizer.tool_registry is registry
    assert team.architect.tool_registry is None
    assert team.reviewer.tool_registry is None


def test_official_simple_agent_runs_with_offline_fake_llm() -> None:
    class FakeLLM:
        def invoke(self, messages, **kwargs) -> str:
            assert messages[-1]["content"] == "请澄清这个需求"
return «Подлежит подтверждению: целевые пользователи и критерии приемки».

    agent = SimpleAgent(
name="Тест интеграции автономной среды",
        llm=FakeLLM(),  # type: ignore[arg-type]
        config=Config(debug=False),
    )

result = Agent.run("Пожалуйста, уточните это требование")

Assert result == «Подлежит подтверждению: целевые пользователи и критерии приемки».


def test_official_simple_agent_can_call_requirement_tool_with_plain_text() -> None:
    class ToolCallingFakeLLM:
        def __init__(self) -> None:
            self.responses = iter(
                [
«[TOOL_CALL:requirement_audit: Создайте апплет регистрации активности для жителей]»,
«Первоначальная проверка требований завершена.»,
                ]
            )
            self.calls = []

        def invoke(self, messages, **kwargs) -> str:
            self.calls.append(messages)
            return next(self.responses)

    fake_llm = ToolCallingFakeLLM()
    agent = SimpleAgent(
name="Инструмент вызывает интеграционный тест",
        llm=fake_llm,  # type: ignore[arg-type]
        config=Config(debug=False),
        tool_registry=create_tool_registry(),
    )

result = Agent.run("Пожалуйста, проверьте полноту требований")

Assert result == «Первоначальная проверка требований завершена».
    assert '"ok": true' in fake_llm.calls[1][-1]["content"]
