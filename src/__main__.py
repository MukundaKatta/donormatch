"""CLI for donormatch."""
import sys, json, argparse
from .core import Donormatch

def main():
    parser = argparse.ArgumentParser(description="DonorMatch — Nonprofit Donor CRM. AI-powered donor matching and fundraising optimization.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Donormatch()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.process(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"donormatch v0.1.0 — DonorMatch — Nonprofit Donor CRM. AI-powered donor matching and fundraising optimization.")

if __name__ == "__main__":
    main()
