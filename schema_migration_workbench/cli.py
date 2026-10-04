import argparse, json
from . import core


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Plan, apply and back up SQLite migrations"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["plan", "apply", "status", "backup"]:
        sub = commands.add_parser(name)
        sub.add_argument("database")
        if name in ["plan", "apply"]:
            sub.add_argument("directory")
        if name == "backup":
            sub.add_argument("target")
    args = parser.parse_args(argv)
    result = (
        core.status(args.database)
        if args.command == "status"
        else (
            core.backup(args.database, args.target)
            if args.command == "backup"
            else getattr(core, args.command)(args.database, args.directory)
        )
    )
    print(json.dumps(result, indent=2))
