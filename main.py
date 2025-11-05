from src.scraper import scraper_main
from src.parser import parse_main
from argparse import ArgumentParser
import sys


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

    match args.commands:
        case "scrape":
            scraper_main()
        case "parse":
            parse_main()
        case _:
            print("Unknown subcommand")
            parser.print_help(sys.stderr)


if __name__ == "__main__":
    main()
