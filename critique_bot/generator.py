import json
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup


# -----------------------------------------
# 1. Saenggeul search
# -----------------------------------------
def search_saenggeul_real(query: str, top_k: int = 5):
    q = quote_plus(query)
    url = f"https://sgsg.hankyung.com/search?query={q}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    results = []
    ul = soup.select_one("ul.search-list")
    if ul:
        items = ul.select("li.item")
        for li in items[:top_k]:
            a = li.select_one("a")
            title = a.get_text(strip=True) if a else ""
            link = a["href"] if (a and a.has_attr("href")) else ""
            if link.startswith("/"):
                link = "https://sgsg.hankyung.com" + link
            desc_el = li.select_one("p, .summary, .desc")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            results.append({"title": title, "link": link, "desc": desc})

    if not results:
        results.append({"title": f"No results for: {query}", "link": url, "desc": ""})
    return results

# -----------------------------------------
# 2. Argument analyzer
# -----------------------------------------
def analyze_argument_kor(user_argument: str, model: str, client) -> dict:
    system_msg = (
        "You are an Argument Analyzer. "
        "Given a Korean argument, output ONLY JSON with keys: main_claim, premises, weak_premises. "
        "weak_premises must contain vague, overgeneralized, or evidence-needing premises."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_argument},
        ],
        temperature=0.2,
    )
    txt = resp.choices[0].message.content.strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {
            "main_claim": user_argument,
            "premises": [user_argument],
            "weak_premises": [user_argument],
        } 
# -----------------------------------------
# 3. Counter generator
# -----------------------------------------
def generate_counter_kor(user_argument: str, analysis: dict, model: str, client):
    # 약한 전제 (공격 대상) 불러오기
    weak = analysis.get("weak_premises", [])

    # 주요 주장 불러오기
    target = weak[0] if weak else analysis.get("main_claim", user_argument)

    # 생글생글 기사 불러오기 (target 으로 검색)
    sg_results = search_saenggeul_real(target, top_k=5)
    sg_text = "\n".join(
        [f"- {r['title']} ({r['link']}) :: {r['desc']}" for r in sg_results]
    )

    system_msg = (
        "You are CritiqueBot. Your job is to WRITE A COUNTERARGUMENT in Korean. "
        "Write the reply in **Korean casual speech (banmal)** "
        "Do not describe the task. Do not evaluate. Actually refute. "
        "Directly attack the target premise using the web snippets. "
        "Max 2 sentences. Be clear and debate-like."
    )
    user_msg = (
        f"[사용자 주장]\n{user_argument}\n\n"
        f"[분석 결과]\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"[공격할 전제]\n{target}\n\n"
        f"[관련 기사 검색 결과]\n{sg_text}\n\n"
        "위 정보를 근거로 위 주장을 반박해줘."
    )
    print("아래 프롬프트를 기반으로 너의 주장을 분석 중!\n", user_msg)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
        max_tokens=200,
    )
    counter = resp.choices[0].message.content.strip()
    return counter, sg_results
