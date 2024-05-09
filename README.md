# h101Login
This is a simple brute force tool created for testing Hacker101 level 3.

```bash
python3 h101_login.py --help

Usage: h101_login.py [OPTIONS]

  This app brute forces login at hacker101 CTF level 3.

Options:
  -u, --url TEXT             Type the target URL.  [required]
  -w, --wordlist PATH        Type the path to wordlist file.  [required]
  -m, --mas_threads INTEGER  Type the number of concurrent threads.
                             [required]
  -v, --valid_string TEXT    Type successful login string.  [required]
  -i, --invalid_string TEXT  Type unsuccessful login string.  [required]
  --help                     Show this message and exit.
```


```bash
python h101Passwd --help

Usage: h101_passwd.py [OPTIONS]

  This app brute forces passwords at hacker101 CTF level 3.

Options:
  -u, --url TEXT             Type the target URL.  [required]
  -l, --username TEXT        Type the number of concurrent threads.
                             [required]
  -w, --wordlist PATH        Type the path to wordlist file.  [required]
  -m, --max_threads INTEGER  Type the number of concurrent threads.
                             [required]
  -v, --valid_string TEXT    Type successful login string.  [required]
  -i, --invalid_string TEXT  Type unsuccessful login string.  [required]
  --help                     Show this message and exit.
```
