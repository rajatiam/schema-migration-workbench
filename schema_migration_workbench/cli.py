import argparse, json
from . import core


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Plan and apply checksummed SQLite migrations"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["plan", "apply", "status"]:
        sub = commands.add_parser(name)
        sub.add_argument("database")
        if name != "status":
            sub.add_argument("directory")
    args = parser.parse_args(argv)
    result = (
        core.status(args.database)
        if args.command == "status"
        else getattr(core, args.command)(args.database, args.directory)
    )
    print(json.dumps(result, indent=2))
