from __future__ import annotations

from newsbot.profile import load_minimized_profile


def test_load_minimized_profile_keeps_positions_but_excludes_returns_and_device(tmp_path) -> None:
    path = tmp_path / "profile.xml"
    path.write_text(
        """
<system_instructions>
  <user_context>
    <profile>
      <basic_info>- 身份: should-not-send</basic_info>
      <tech_stack>- Active Matter and C++</tech_stack>
      <environment>- PC: MacBook Air</environment>
    </profile>
    <business_status>
      <entity_type>学生, 风险承受能力一般</entity_type>
      <stock_investment>- 投资风格: 定投</stock_investment>
      <stock_positions>- MSFT: 11.77%</stock_positions>
      <stock_rate_of_return>- rate of return of last year: 13.3%</stock_rate_of_return>
    </business_status>
  </user_context>
  <tool_use_policy>
    <search_protocol>宏观与金融</search_protocol>
    <output_constraints>严格使用某种工具策略</output_constraints>
  </tool_use_policy>
</system_instructions>
""".strip(),
        encoding="utf-8",
    )

    summary = load_minimized_profile(str(path))

    assert "Active Matter" in summary
    assert "MSFT: 11.77%" in summary
    assert "定投" in summary
    assert "13.3%" not in summary
    assert "rate of return" not in summary
    assert "MacBook" not in summary
    assert "should-not-send" not in summary
    assert "宏观与金融" not in summary
    assert "工具策略" not in summary
    assert "<system_instructions>" not in summary
