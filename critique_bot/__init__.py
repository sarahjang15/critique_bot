"""
CritiqueBot - 생글생글 기반 토론 챗봇
"""

__version__ = "0.1.0"

from critique_bot.evaluator import evaluate_counter_kor
from critique_bot.generator import (
    search_saenggeul_real,
    analyze_argument_kor,
    generate_counter_kor
)

__all__ = [
    "evaluate_counter_kor",
    "search_saenggeul_real",
    "analyze_argument_kor",
    "generate_counter_kor",
]

