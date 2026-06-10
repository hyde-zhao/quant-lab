"""通用权益因子定义注册表。

本模块只保存项目内可复用的因子身份、方向、输入和来源元数据。
书籍章节、论文或实验编号只能作为 source_refs，不作为因子 ID 命名空间。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from engine.multifactor_contracts import FactorDirection, FactorSpec


FACTOR_LIBRARY_SCHEMA = "factor_library_v1"
EQUITY_CORE_FACTOR_SET_ID = "equity_core_factor_set_v1"

DEFAULT_EQUITY_CORE_FACTOR_IDS = (
    "market_beta_252",
    "size_total_market_cap",
    "value_bm",
    "momentum_12_1",
    "profitability_roe_ttm",
    "investment_asset_growth",
    "abnormal_turnover_21_252",
)


@dataclass(frozen=True, slots=True)
class EquityFactorDefinition:
    factor_id: str
    name: str
    category: str
    raw_variable: str
    direction: str
    input_fields: tuple[str, ...]
    formula: str
    default_window: int | Mapping[str, Any]
    source_refs: tuple[str, ...]
    implementation_note: str = ""
    schema_version: str = FACTOR_LIBRARY_SCHEMA

    @property
    def book_name(self) -> str:
        """兼容第三章复刻文档中的中文因子名称。"""

        return self.name

    @property
    def required_inputs(self) -> tuple[str, ...]:
        """兼容旧的第三章复刻入口命名。"""

        return self.input_fields

    @property
    def chapter_section(self) -> str:
        """返回第三章来源段落；通用因子身份本身不绑定章节。"""

        for ref in self.source_refs:
            if ref.startswith("book:factor_investing:chapter3:"):
                return ref.rsplit(":", maxsplit=1)[-1]
        return ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_equity_factor_definition(definition: EquityFactorDefinition) -> tuple[str, ...]:
    """校验单个因子定义是否满足长期因子库最小合同。"""

    issues: list[str] = []
    if not definition.factor_id:
        issues.append("factor_id 不能为空")
    if definition.factor_id.startswith("chapter"):
        issues.append("factor_id 不得使用书籍章节作为命名空间")
    if not definition.factor_id.replace("_", "").replace("-", "").isalnum():
        issues.append("factor_id 只能包含字母、数字、下划线或连字符")
    if not definition.name:
        issues.append("name 不能为空")
    if definition.direction not in {item.value for item in FactorDirection}:
        issues.append("direction 必须是 positive/negative/neutral/custom")
    if not definition.input_fields:
        issues.append("input_fields 不能为空")
    if not definition.formula:
        issues.append("formula 不能为空")
    if not definition.source_refs:
        issues.append("source_refs 不能为空")
    return tuple(issues)


def validate_equity_factor_library(definitions: Mapping[str, EquityFactorDefinition] | Sequence[EquityFactorDefinition]) -> dict[str, tuple[str, ...]]:
    """校验因子库并返回有问题的因子。"""

    items = definitions.values() if isinstance(definitions, Mapping) else definitions
    seen: set[str] = set()
    issues_by_factor: dict[str, tuple[str, ...]] = {}
    for definition in items:
        issues = list(validate_equity_factor_definition(definition))
        if definition.factor_id in seen:
            issues.append("factor_id 重复")
        seen.add(definition.factor_id)
        if issues:
            issues_by_factor[definition.factor_id or "<missing>"] = tuple(issues)
    return issues_by_factor


def equity_core_factor_definitions() -> tuple[EquityFactorDefinition, ...]:
    """返回项目通用权益因子定义。

    这批因子当前来源于《因子投资：方法与实践》第三章复刻，但因子 ID
    使用通用语义，后续其他研究可以复用同一身份。
    """

    return (
        EquityFactorDefinition(
            factor_id="market_beta_252",
            name="市场因子",
            category="market",
            raw_variable="滚动 252 日市场 beta",
            direction="neutral",
            input_fields=("prices.adjusted_close|close", "market_cap.market_cap 可选"),
            formula="cov(stock_return, market_return) / var(market_return)",
            default_window=252,
            source_refs=("book:factor_investing:chapter3:3.2",),
            implementation_note="市场组合收益单独输出为 market_factor_return；beta 可用于 CAPM 截面检验。",
        ),
        EquityFactorDefinition(
            factor_id="size_total_market_cap",
            name="规模因子",
            category="size",
            raw_variable="总市值",
            direction="negative",
            input_fields=("market_cap.market_cap",),
            formula="log(total_market_cap)",
            default_window=1,
            source_refs=("book:factor_investing:chapter3:3.3",),
            implementation_note="打分方向统一为值越大越看多，因此规模 raw 值后续方向取负。",
        ),
        EquityFactorDefinition(
            factor_id="value_bm",
            name="价值因子",
            category="value",
            raw_variable="BM",
            direction="positive",
            input_fields=("financials.book_equity 或 prices/book_to_market", "market_cap.market_cap"),
            formula="book_equity / total_market_cap",
            default_window=1,
            source_refs=("book:factor_investing:chapter3:3.4",),
        ),
        EquityFactorDefinition(
            factor_id="momentum_12_1",
            name="动量因子",
            category="momentum",
            raw_variable="过去 12 到 1 个月累计收益",
            direction="positive",
            input_fields=("prices.adjusted_close|close",),
            formula="close[t-21] / close[t-252] - 1",
            default_window={"lookback": 252, "skip_recent": 21},
            source_refs=("book:factor_investing:chapter3:3.5",),
            implementation_note="用日频近似月频，排除最近 21 个交易日。",
        ),
        EquityFactorDefinition(
            factor_id="profitability_roe_ttm",
            name="盈利因子",
            category="profitability",
            raw_variable="ROE(TTM)",
            direction="positive",
            input_fields=("financials.roe_ttm 或 operating_profit_ttm/最近四个报告期平均股东权益",),
            formula="operating_profit_ttm / mean(last_4_report_period_book_equity)",
            default_window=1,
            source_refs=("book:factor_investing:chapter3:3.6",),
        ),
        EquityFactorDefinition(
            factor_id="investment_asset_growth",
            name="投资因子",
            category="investment",
            raw_variable="总资产增长率",
            direction="negative",
            input_fields=("financials.asset_growth 或年报 total_assets",),
            formula="annual_report_total_assets / lag_annual_report_total_assets - 1",
            default_window=252,
            source_refs=("book:factor_investing:chapter3:3.7",),
            implementation_note="打分方向统一为低投资更高分，因此 raw 值后续方向取负。",
        ),
        EquityFactorDefinition(
            factor_id="abnormal_turnover_21_252",
            name="换手率因子",
            category="turnover",
            raw_variable="异常换手率",
            direction="negative",
            input_fields=("market_cap.turnover_rate 或 prices.turnover_rate",),
            formula="mean(turnover_rate, 21) / mean(turnover_rate, 252)",
            default_window={"short": 21, "long": 252},
            source_refs=("book:factor_investing:chapter3:3.8",),
            implementation_note="打分方向统一为低异常换手率更高分，因此 raw 值后续方向取负。",
        ),
    )


def equity_core_factor_definition_map() -> dict[str, EquityFactorDefinition]:
    return {item.factor_id: item for item in equity_core_factor_definitions()}


def build_equity_factor_library(
    additional_definitions: Sequence[EquityFactorDefinition] = (),
    *,
    duplicate_policy: str = "fail",
) -> dict[str, EquityFactorDefinition]:
    """构建可扩展因子库。

    `duplicate_policy`:
    - `fail`: 发现重复因子时报错。
    - `replace`: 允许 additional definition 覆盖核心定义。
    """

    if duplicate_policy not in {"fail", "replace"}:
        raise ValueError("duplicate_policy 只能是 fail/replace")
    library = equity_core_factor_definition_map()
    for definition in additional_definitions:
        issues = validate_equity_factor_definition(definition)
        if issues:
            raise ValueError(f"因子定义无效 {definition.factor_id}: " + "; ".join(issues))
        if definition.factor_id in library and duplicate_policy == "fail":
            raise ValueError(f"重复因子定义: {definition.factor_id}")
        library[definition.factor_id] = definition
    return library


def get_equity_factor_definition(factor_id: str) -> EquityFactorDefinition:
    definitions = equity_core_factor_definition_map()
    if factor_id not in definitions:
        raise KeyError(f"未知因子: {factor_id}")
    return definitions[factor_id]


def to_factor_specs(
    definitions: Mapping[str, EquityFactorDefinition] | Sequence[EquityFactorDefinition],
    *,
    version: str = "v1",
    universe: str | Mapping[str, Any] = "project_research_universe",
) -> tuple[FactorSpec, ...]:
    items = definitions.values() if isinstance(definitions, Mapping) else definitions
    return tuple(to_factor_spec(definition, version=version, universe=universe) for definition in items)


def to_factor_spec(
    definition: EquityFactorDefinition,
    *,
    version: str = "v1",
    universe: str | Mapping[str, Any] = "project_research_universe",
    preprocessing: Mapping[str, Any] | None = None,
    availability_policy: Mapping[str, Any] | None = None,
    data_lineage: Mapping[str, Any] | None = None,
) -> FactorSpec:
    """把通用因子定义导出为 CR030 `FactorSpec`。"""

    return FactorSpec(
        factor_id=definition.factor_id,
        name=definition.name,
        version=version,
        direction=FactorDirection(definition.direction),
        input_fields=definition.input_fields,
        window=definition.default_window,
        params={
            "formula": definition.formula,
            "category": definition.category,
            "raw_variable": definition.raw_variable,
            "source_refs": definition.source_refs,
            "implementation_note": definition.implementation_note,
        },
        preprocessing=preprocessing
        or {
            "winsorize": "1/99 cross_section",
            "standardize": "zscore cross_section",
            "directional_score": "larger_is_more_bullish",
        },
        universe=universe,
        availability_policy=availability_policy
        or {
            "point_in_time": True,
            "available_at_required": True,
            "no_external_truth": True,
        },
        data_lineage=data_lineage
        or {
            "source_dataset": "local_research_input",
            "research_input_schema": "research_input_v1",
            "evidence_refs": ("engine.factor_library",) + definition.source_refs,
            "source_of_truth": "project_factor_library",
            "factor_set_id": EQUITY_CORE_FACTOR_SET_ID,
            "source_refs": definition.source_refs,
        },
        blocked_claims=("production_truth", "qmt_ready", "simulation_ready", "live_ready"),
        failure_policy="fail_closed",
    )
