# setup
import os
import argparse
from pathlib import Path
from openai import OpenAI
from critique_bot.evaluator import evaluate_counter_kor
from critique_bot.generator import search_saenggeul_real, analyze_argument_kor, generate_counter_kor

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
API_KEY_PATH = SCRIPT_DIR / "api_key.txt"

with open(API_KEY_PATH, "r") as key_file:
    os.environ["OPENAI_API_KEY"] = key_file.read().strip()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# -----------------------------------------
# Main loop
# -----------------------------------------
def run_critiquebot(model: str = "gpt-4o-mini"):
    print(f"📢 크리틱봇 (생글생글 기반) 시작합니다. [model={model}]")
    while True:
        user_arg = input("\n당신의 주장 (끝내려면 '그만'): ").strip()
        if user_arg == "그만":
            print("대화를 종료합니다.")
            break

        analysis = analyze_argument_kor(user_arg, model=model, client=client)
        counter, sg_results = generate_counter_kor(user_arg, analysis, model=model, client=client)

        print("\n🤖 봇의 반박:")
        print(counter)

        print("\n🔗 참조 링크:")
        for r in sg_results:
            print(f"- {r['title']}: {r['link']}")

        # inner loop: keep debating on current topic
        while True:
            print("\n다음 중 선택하세요:")
            print("1) 지금 봇의 반박에 다시 반박하기")
            print("2) 이 주장/반박에 대한 평가·코칭 받기")
            print("3) 새로운 주장으로 다시 시작하기")
            print("4) 종료하기")
            choice = input("번호: ").strip()

            if choice == "1":
                user_arg = input("\n당신의 재반박: ").strip()
                if user_arg == "그만":
                    print("대화를 종료합니다.")
                    return
                analysis = analyze_argument_kor(user_arg, model=model, client=client)
                counter, sg_results = generate_counter_kor(user_arg, analysis, model=model, client=client)
                print("\n🤖 봇의 반박:")
                print(counter)
                print("\n🔗 참조 링크:")
                for r in sg_results:
                    print(f"- {r['title']}: {r['link']}")
            elif choice == "2":
                eval_res = evaluate_counter_kor(user_arg, counter, model=model, client=client)
                print("\n📊 평가 결과:")
                print(eval_res)
                fb = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an argument coach. Give specific Korean suggestions to strengthen the user's argument."
                        },
                        {"role": "user", "content": f"이 주장을 더 설득력 있게 만들려면 어떻게 바꿔야 할까?\n{user_arg}"},
                    ],
                    temperature=0.4,
                )
                print("\n📝 코칭:")
                print(fb.choices[0].message.content.strip())
            elif choice == "3":
                # break inner loop -> go to outer for new topic
                break
            else:
                print("대화를 종료합니다.")
                return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="크리틱봇 - 생글생글 기반 토론 챗봇",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py                              # 기본 모델(gpt-4o-mini) 사용
  python main.py --model gpt-4o               # GPT-4o 모델 사용
  python main.py --model gpt-4o-mini          # GPT-4o-mini 모델 사용
  python main.py -m gpt-4                     # GPT-4 모델 사용 (단축 옵션)
        """
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4o-mini",
        help="사용할 OpenAI 모델 (기본값: gpt-4o-mini)"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 사용 모델: {args.model}")
    run_critiquebot(model=args.model)
