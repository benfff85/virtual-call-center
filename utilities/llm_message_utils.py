import re

def sanitize_message(msg: str, ) -> str:

    # remove non-ascii characters
    msg = re.sub(r'[^\x00-\x7F]+', '', msg)

    # remove Markdown formatting
    msg = re.sub(r"\*\*.*?\*\*", "", msg)

    # remove thinking tags from DeepSeek
    if "</think>" in msg:
        msg = msg.split("</think>")[-1]

    # remove leading and trailing whitespace
    msg = msg.strip()

    return msg