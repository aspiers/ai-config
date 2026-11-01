"""Shared shell-command parsing for the ai-guard-* PreToolUse hooks."""

from __future__ import annotations

import shlex

# Commands that run their arguments as another command.
WRAPPERS = {"command", "env", "exec", "nice", "nohup", "sudo", "time"}


def segments(command: str) -> list[list[str]]:
    """Split a shell command line into simple commands, as token lists.

    Raises ValueError on unbalanced quotes.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    result: list[list[str]] = [[]]
    for token in lexer:
        if set(token) <= set(";&|()\n"):
            result.append([])
        else:
            result[-1].append(token)
    return [seg for seg in result if seg]


def command_words(tokens: list[str], override: str) -> list[str] | None:
    """Return the words of the command `tokens` runs, after any leading
    VAR=value assignments and wrappers such as `env` or `sudo`.

    Returns None when an assignment sets `override` to 1, so the caller
    lets that one command through.
    """
    i = 0
    while i < len(tokens) and "=" in tokens[i] and not tokens[i].startswith("-"):
        if tokens[i] == f"{override}=1":
            return None
        i += 1
    while i < len(tokens) and tokens[i] in WRAPPERS:
        i += 1
        while i < len(tokens) and (tokens[i].startswith("-") or "=" in tokens[i]):
            if tokens[i] == f"{override}=1":
                return None
            i += 1
    return tokens[i:]
