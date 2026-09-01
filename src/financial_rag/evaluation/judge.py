"""LLM-as-judge for evaluating answer faithfulness."""

import re

import groq as groq_sdk


_JUDGE_PROMPT = """\
Evaluate if the answer is faithful to the source context blocks below.

Question: {question}

Source context blocks:
{contexts}

Answer given:
{answer}

Rate the faithfulness on this scale:
0 = Answer contradicts sources or invents information not in the context blocks
1 = Answer is partially grounded but contains unsupported claims or inferences
2 = Answer is mostly grounded with minor unsupported additions
3 = Answer is fully grounded — every claim traces back to the context blocks,
    or correctly states that information is not available

Rules:
- Compare each claim in the answer against the context blocks literally.
- General background or inferences not in the blocks count as unsupported (max score 2).
- If contexts are empty and the answer says "no information found", rate 3.
- If contexts are empty but the answer makes specific claims, rate 0.
- Respond with ONLY a single digit: 0, 1, 2, or 3. Nothing else.\
"""


def judge_faithfulness(
    question: str,
    answer: str,
    citations: list[str],
    contexts: list[str] | None = None,
    judge_model: str = "llama-3.1-8b-instant",
) -> tuple[int, str]:
    """Score answer faithfulness using a Groq model as judge.

    Args:
        question: The original question.
        answer: The generated answer to evaluate.
        citations: List of citation strings from the retriever.
        contexts: Actual chunk texts to evaluate against (preferred over citations).
        judge_model: Groq model to use as judge (default: fast llama instant model).

    Returns:
        Tuple of (score 0-3, raw judge response for debugging).
    """
    if contexts:
        contexts_text = "\n\n".join(
            f"[{i+1}] {c[:700]}" for i, c in enumerate(contexts)
        )
    elif citations:
        contexts_text = "\n".join(f"- {c}" for c in citations)
    else:
        contexts_text = "(none)"

    prompt = _JUDGE_PROMPT.format(
        question=question,
        contexts=contexts_text,
        answer=answer[:800],
    )

    try:
        client = groq_sdk.Groq()
        response = client.chat.completions.create(
            model=judge_model,
            max_tokens=64,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content.strip()
        # Extract score from the TAIL of the response (last 300 chars).
        tail = raw[-300:]
        verdict_matches = list(re.finditer(
            r"(?:score|answer|verdict|rating)[:\s*]+([0-3])\b", tail, re.IGNORECASE
        ))
        if verdict_matches:
            score = int(verdict_matches[-1].group(1))
        else:
            all_digits = list(re.finditer(r"(?<!\d)([0-3])(?!\d)", tail))
            score = int(all_digits[-1].group(1)) if all_digits else 1
        return score, raw
    except Exception as e:
        return 1, f"judge error: {e}"
