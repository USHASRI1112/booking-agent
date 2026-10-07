"""
Chat with the scheduling agent in your terminal:   python main.py
"""
from app.agent import Agent
from app.improvement.reinforcement import load_rules


def main():
    agent = Agent(load_rules())  # uses any rules the improvement loop has learned

    print("Riverside Family Clinic scheduling assistant (Ctrl-C to quit)")
    print("Test patients: Maria Lopez 1985-03-12 | James Chen 1972-11-30 | Aisha Khan 1990-07-21\n")

    while True:
        try:
            patient_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if patient_text:
            agent_text = agent.reply(patient_text)
            print("agent>", agent_text, "\n")


if __name__ == "__main__":
    main()
