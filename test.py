#!/usr/bin/env python3
# test.py

import concurrent.futures
from queue import Queue

from rich.console import Console
from rich.progress import Progress

c = Console()


def read_from_wordlist(wordlist_file):
    with open(wordlist_file, "r") as wfile:
        return [word.strip() for word in wfile.readlines() if word.strip() != ""]


def print_words(username, word_queue, total_words):
    progress = Progress()
    task = progress.add_task(f"Brute forcing username '{username}'->",
                             total=total_words,
                             fields="Progress")

    with c.screen():

        progress.start()
        while not word_queue.empty():
            word = word_queue.get()
            if word == username:
                # c.print(f"\nFound password: {word}\n")
                found_password = word
                # break
            # else:
            #     c.update_screen_lines([10][1])

            progress.update(task, advance=1)
        progress.stop()
        c.input("Press enter to continue...")
    c.print(f"Found_password: {found_password}")


def main():
    word_queue = Queue()
    wordlist = read_from_wordlist("users.txt")
    for word in wordlist:
        word_queue.put(word)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.submit(print_words, "delbert", word_queue, len(wordlist))


if __name__ == "__main__":
    main()
