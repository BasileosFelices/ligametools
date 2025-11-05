import sys
from argparse import ArgumentParser
from importlib import metadata

from src.config import load_config
from src.parser import parse_main
from src.scraper import scraper_main


def create_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="ligametools",
        description="LinkedIn games helper tools",
    )

    commands = parser.add_subparsers(dest="commands", help="List available commands")

    scraper_parser = commands.add_parser(
        "scrape", help="Reads and downloads the leaderboard"
    )

    parser_parser = commands.add_parser(
        "parse", help="Parses read html into readable output"
    )

    return parser


def main():
    parser = create_arg_parser()
    args = parser.parse_args()

    config = load_config()

    match args.commands:
        case "scrape":
            scraper_main(config)
        case "parse":
            parse_main()
        case _:
            print(metadata.metadata("ligametools"))
            print("Unknown subcommand")
            parser.print_help(sys.stderr)


if __name__ == "__main__":
    main()
