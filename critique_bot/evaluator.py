import json


def evaluate_counter_kor(original: str, candidate: str, model: str, client) -> dict:
    """Evaluate a counterargument against an original argument."""
    
    system = "You are an argument evaluator. Return ONLY valid JSON."
    user = f"""You are a strict debate evaluator. Score a Korean counterargument using ONLY JSON.

Evaluate the COUNTERARGUMENT against the ORIGINAL ARGUMENT on six criteria, each scored 0–100 (integers).

[Criteria]
1) premise_targeting — Does the counter directly attack a weak/critical (possibly implicit) premise of the original?
2) stance_opposition — Is the counter clearly in opposition to the original stance?
3) specificity — Does it provide concrete mechanisms, facts, or examples (even if no explicit citation is given)?
4) logical_soundness — Avoids fallacies (strawman, red herring, over-generalization), maintains valid reasoning.
5) coherence — Flows logically with no internal contradictions.
6) conciseness — Delivers the key point(s) clearly in 1–2 sentences.

[Output JSON schema]
{{
  "final_score": <0-100 integer>,
  "subscores": {{
    "premise_targeting": <0-100>,
    "stance_opposition": <0-100>,
    "specificity": <0-100>,
    "logical_soundness": <0-100>,
    "coherence": <0-100>,
    "conciseness": <0-100>
  }},
  "analysis": "<brief rationale in Korean (1–2 sentences)>"
}}

Compute and return ONLY the JSON. No extra text.

[Original]
{original}

[Counterargument]
{candidate}
"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    # Use OpenAI client to generate response
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=320,
        temperature=0.0
    )
    txt = resp.choices[0].message.content.strip()

    try:
        out = json.loads(txt)
    except json.JSONDecodeError:
        # Minimal safe shape if the model replies non-JSON
        out = {
            "final_score": 0,
            "subscores": {
                "premise_targeting": 0,
                "stance_opposition": 0,
                "specificity": 0,
                "logical_soundness": 0,
                "coherence": 0,
                "conciseness": 0
            },
            "analysis": "JSON 파싱 실패로 기본 점수를 반환합니다."
        }

    # Ensure final_score exists; compute weighted sum if missing
    subs = out.get("subscores", {})
    if "final_score" not in out or not isinstance(out["final_score"], (int, float)):
        weights = {
            "premise_targeting": 0.35,
            "stance_opposition": 0.15,
            "specificity": 0.15,
            "logical_soundness": 0.15,
            "coherence": 0.10,
            "conciseness": 0.10
        }
        final = 0.0
        for k, w in weights.items():
            final += w * float(subs.get(k, 0))
        out["final_score"] = round(final)

    return out
