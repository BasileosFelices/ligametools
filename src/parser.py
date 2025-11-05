import os
import re
from typing import TypedDict

from bs4 import BeautifulSoup

time_regex = re.compile(r"^\d+:\d+$")


class GameTimeEntry(TypedDict):
    name: str
    time: str
    flawless: bool


def parse_leaderboard(html_text: str) -> list[GameTimeEntry]:
    soup = BeautifulSoup(html_text, "html.parser")

    leaderboard_entries = soup.find_all(
        "div", class_="pr-connections-leaderboard-player__container"
    )

    results: list[GameTimeEntry] = []

    for entry in leaderboard_entries:
        name_element = entry.find(
            "div", class_="pr-connections-leaderboard-player__text-wrapper"
        ).find("div", class_="text-body-medium-bold")

        # Find all spans with this class (will get rank AND time)
        time_element = None
        potential_spans = entry.find_all("span", class_="text-body-medium")
        for span in potential_spans:
            text = span.get_text(strip=True)
            # Use regex to see if the text matches the time format
            if time_regex.match(text):
                time_element = span
                break  # Stop once we've found the time

        # 3. Check for "bezchybny vykon"
        subtitle_tag = entry.find(
            "div", class_="pr-connections-leaderboard-player__subtitle"
        )
        # Check if the tag exists and if its lowercase text contains "bezchybn"
        # This is robust to capitalization, diacritics, and the diamond emoji
        flawless = bool(subtitle_tag and "bezchybn" in subtitle_tag.get_text().lower())

        if name_element and time_element:
            name = str(name_element.text.strip())
            time = str(time_element.text.strip())

            results.append({"name": name, "time": time, "flawless": flawless})

    return results


def parse_main():
    HTML_OUT_FOLDER = "leaderboards_out"

    files = os.listdir(HTML_OUT_FOLDER)

    for file in files:
        filepath = f"{HTML_OUT_FOLDER}/{file}"
        with open(filepath, "r", encoding="utf8") as f:
            html_text = f.read()
            print(file)
            print(parse_leaderboard(html_text))
