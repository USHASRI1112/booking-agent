"""
The evaluation + improvement loop.

    python run_eval.py                                   # baseline, then up to 2 improvement rounds
    python run_eval.py --rounds 3                        # more rounds
    python run_eval.py --reset                           # forget learned rules, start from the base prompt
    python run_eval.py --only emergency,happy_book       # run only some scenarios (faster / cheaper)

THE LOOP:
    1. Run all scenarios with the current rules        -> score BEFORE
    2. If something failed, ask an AI to propose ONE new rule from the failures
    3. Run all scenarios again with that rule added    -> score AFTER
    4. Keep the rule only if the score went up AND nothing that passed before broke
    5. Repeat
"""
import argparse

from app.evaluation.evaluator import run_suite
from app.improvement.analyzer import propose_rule
from app.improvement.policy import should_keep_rule
from app.improvement.reinforcement import load_rules, save_rules


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--only", help="comma-separated scenario ids")
    args = parser.parse_args()

    only_ids = args.only.split(",") if args.only else None
    if args.reset:
        save_rules([])

    # Step 1: baseline
    rules = load_rules()
    score, results = run_suite(rules, "baseline", only_ids)

    for round_number in range(1, args.rounds + 1):
        failed = [result for result in results if not result["pass"]]
        if not failed:
            print("\nAll scenarios pass. Nothing to improve.")
            break

        # Step 2: propose a rule from the failures
        new_rule = propose_rule(failed, rules)
        print(f"\n--- round {round_number}: proposed rule ---")
        print(f"  root cause: {new_rule['root_cause']}")
        print(f"  rule:       {new_rule['rule']}")
        print(f"  targets:    {new_rule['addresses']}")

        # Step 3: re-run everything with the rule added
        candidate_rules = rules + [new_rule]
        new_score, new_results = run_suite(candidate_rules, f"round{round_number}", only_ids)

        # Step 4: keep or throw away
        keep, regressions = should_keep_rule(results, new_results)
        if keep:
            rules = candidate_rules
            save_rules(rules)
            print(f"  ACCEPTED: {score:.0%} -> {new_score:.0%}, no regressions. Saved to data/reinforcements.json")
            score, results = new_score, new_results
        else:
            print(f"  REJECTED: {score:.0%} -> {new_score:.0%}, regressions: {regressions or 'none'}. Rule discarded.")

    print(f"\nFinal score: {score:.0%} with {len(rules)} learned rule(s).")


if __name__ == "__main__":
    main()
