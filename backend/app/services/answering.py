from dataclasses import dataclass, field
from time import perf_counter

from app.providers.base import LLMProvider, ProviderError
from app.services.citation import has_valid_citations
from app.services.retrieval import RetrievalResult, Source


@dataclass(frozen=True, slots=True)
class AnswerResult:
    answer: str
    sources: list[Source]
    grounded: bool
    timings_ms: dict[str, float] = field(default_factory=dict)


class AnsweringService:
    def __init__(self, llm: LLMProvider | None) -> None:
        self.llm = llm

    def answer(self, question: str, retrieval: RetrievalResult) -> AnswerResult:
        started = perf_counter()
        if not retrieval.sources:
            return self._result(
                "当前知识库证据不足，建议补充相关岗位 JD、官方文档或学习资料后再试。",
                retrieval,
                grounded=False,
                llm_ms=0.0,
                started=started,
            )

        if self.llm is None:
            return self._result(
                "已检索到相关资料，但尚未配置在线 LLM，请直接查看下方来源。",
                retrieval,
                grounded=False,
                llm_ms=0.0,
                started=started,
            )

        prompt = self._prompt(question, retrieval.sources)
        llm_started = perf_counter()
        try:
            answer = self.llm.complete(prompt)
            if not has_valid_citations(answer, retrieval.sources):
                answer = self.llm.complete(
                    prompt
                    + [
                        {
                            "role": "assistant",
                            "content": answer,
                        },
                        {
                            "role": "user",
                            "content": "引用无效。仅使用给出的来源 ID 修复答案，并保留行内引用。",
                        },
                    ]
                )
            valid = has_valid_citations(answer, retrieval.sources)
            if not valid:
                answer = "已检索到相关资料，但暂时无法生成可靠引用，请直接查看下方来源。"
            return self._result(
                answer,
                retrieval,
                grounded=valid,
                llm_ms=(perf_counter() - llm_started) * 1000,
                started=started,
            )
        except ProviderError:
            return self._result(
                "已检索到相关资料，但在线 LLM 暂时无法生成答案，请直接查看下方来源。",
                retrieval,
                grounded=False,
                llm_ms=(perf_counter() - llm_started) * 1000,
                started=started,
            )

    @staticmethod
    def _prompt(question: str, sources: list[Source]):
        evidence = "\n\n".join(
            f"[{source.source_id}] {source.filename}\n{source.text}" for source in sources
        )
        return [
            {
                "role": "system",
                "content": (
                    "你是求职知识库助手。只能依据提供的来源回答；事实结论必须使用 "
                    "[S1] 格式行内引用。资料未明确说明时要写明这是建议，不得编造。"
                ),
            },
            {"role": "user", "content": f"问题：{question}\n\n来源：\n{evidence}"},
        ]

    @staticmethod
    def _result(
        answer: str,
        retrieval: RetrievalResult,
        *,
        grounded: bool,
        llm_ms: float,
        started: float,
    ) -> AnswerResult:
        timings = dict(retrieval.timings_ms)
        timings["llm"] = round(llm_ms, 2)
        timings["total"] = round((perf_counter() - started) * 1000, 2)
        return AnswerResult(answer, retrieval.sources, grounded, timings)
