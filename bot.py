import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from datetime import date
import requests
from db import Session, PlayerSession
import string

load_dotenv()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


# load in valid guesses
with open('valid-wordle-words.txt', 'r') as file:
    valid_guesses = {line.strip() for line in file}


def fetch_word():
    global today
    response = requests.get(f"https://www.nytimes.com/svc/wordle/v2/{date.today()}.json")
    return response.json()["solution"]


def check_guess(guess):
    daily_word = fetch_word()

    if guess not in valid_guesses:
        return "Not in word list"
    
    check_string = []
    yellows = []

    # fill greens
    for i, letter in enumerate(guess):
        if letter == daily_word[i]:
            yellows.append(letter)
            check_string.append("🟩")
            continue
        check_string.append("⬜")
    
    #fill yellows
    for i, letter in enumerate(guess):
        if check_string[i] == "🟩":
            continue
        if letter in daily_word:
            # consider if yellows for this letter have already been given
            if daily_word.count(letter) > yellows.count(letter):
                yellows.append(letter)
            else:
                check_string[i] = "⬜"
                continue
            check_string[i] = "🟨"
    
    return "".join(check_string)

@app.command("/wordle")
def handle_guess(ack, respond, command):
    ack()
    raw_guess = command.get("text", "")

    if not raw_guess:
        respond("hey bud... you forgot your guess. try `/wordle <guess here>`")
        return
    
    # process raw guess
    user_guess = raw_guess.strip().lower()

    if len(user_guess) != 5 or not user_guess.isalpha():
        respond("hey bud... that's not 5 letters")
        return

    # get guess string!
    guess_string = check_guess(user_guess)

    if guess_string == "Not in word list":
        respond("that word isn't in our word list... try again bud")
        return

    # let's talk to the db now
    db = Session()

    player = db.query(PlayerSession).filter_by(slack_user_id=command['user_id']).first()
    if not player:
        player = PlayerSession(slack_user_id=command['user_id'])
        db.add(player)
        player.greens = ""
        player.grays = ""
        player.yellows = ""
    elif player.play_date != date.today():
        player.play_date = date.today()
        player.guesses = ""
        player.guess_strings = ""
        player.done = False
        player.greens = ""
        player.yellows = ""
        player.grays = ""

    # process greens, yellows, grays
    for i in range(len(guess_string)):
        if guess_string[i] == "🟩":
            player.greens += user_guess[i].upper()
        elif guess_string[i] == "🟨":
            player.yellows += user_guess[i].upper()
        elif guess_string[i] == "⬜":
            player.grays += user_guess[i].upper()

    # cleanup letters
    green_set = set(player.greens)
    yellow_set = set(player.yellows)
    gray_set = set(player.grays)
    yellow_set = yellow_set - green_set
    player.greens = "".join(green_set)
    player.yellows = "".join(yellow_set)
    player.grays = "".join(gray_set)

    if not player.done:
        if not player.guesses:
            player.guesses = user_guess
            player.guess_strings = guess_string
        else:
            player.guesses += f",{user_guess}"
            player.guess_strings += f",{guess_string}"

        db.commit()

    # get guess history
    guess_list = player.guesses.split(",")
    string_list = player.guess_strings.split(",")

    if not player.done:
        replypend = f"*guess {len(guess_list)}/6:*\n\n"
    else:
        replypend = "*you already finished! here's how you did!*\n\n"

    reply = ""
    reply_pub = ""

    for count, guess in enumerate(guess_list):
        reply += f"{guess.upper()}: {string_list[count]}\n"
        reply_pub += f"{string_list[count]}\n"

    if len(guess_list) == 6 or guess_string == "🟩🟩🟩🟩🟩":
        player.done = True
        db.commit()

        respond(
        text="your wordle results",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": replypend + reply
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "share to channel"
                        },
                        "style": "primary",
                        "value": reply_pub,
                        "action_id": "share_result_button"
                    }
                ]
            }
        ]
    )
    else:
        respond(replypend + reply)

    db.close()
    return

@app.action("share_result_button")
def handle_share_button(ack, body, client, respond):
    ack()

    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]

    shared_text = body["actions"][0]["value"]

    guess_amt = "X" if "🟩🟩🟩🟩🟩" not in shared_text else len(shared_text.splitlines())
    wordle_number = int(requests.get(f"https://www.nytimes.com/svc/wordle/v2/{date.today()}.json").json()["days_since_launch"])
    try:
        client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> - Wordle {wordle_number:,} {guess_amt}/6\n\n{shared_text}"
        )
    except Exception as e:
        if "channel_not_found" in str(e):
            respond("hey i'm not in this channel bud. invite me to the channel by using `/invite @Wordle for Slack` and then try again.")
            return
        else:
            raise
    
    respond(
        text="your result was shared to the channel!!!",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": shared_text + "\n\n_shared to channel_"
                }
            }
        ],
        replace_original=True
    )
    return


@app.command("/wordle-share")
def handle_share(ack, respond, command, client):
    ack()

    user_id = command['user_id']
    channel_id = command['channel_id']

    db = Session()

    player = db.query(PlayerSession).filter_by(slack_user_id=command['user_id']).first()

    if not player:
        respond("you haven't played wordle yet! finish today's wordle, and then you can share your results :thinking:")
        return
    if not player.done:
        respond("you haven't finished today's wordle yet! finish today's wordle, and then you can share your results :thinking:")
        return

    guess_list = player.guesses.split(",")
    string_list = player.guess_strings.split(",")

    guess_amt = "X" if "🟩🟩🟩🟩🟩" not in string_list else len(guess_list)
    wordle_number = int(requests.get(f"https://www.nytimes.com/svc/wordle/v2/{date.today()}.json").json()["days_since_launch"])

    public_guess_strings = ""
    for i in string_list:
        public_guess_strings += f"{i}\n"

    try:
        client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> - Wordle {wordle_number:,} {guess_amt}/6\n\n{public_guess_strings}"
        )
    except Exception as e:
        if "channel_not_found" in str(e):
            respond("hey i'm not in this channel bud. invite me to the channel by using `/invite @Wordle for Slack` and then try again.")
            return
        else:
            raise

    respond("your result was shared to the channel!!!")
    return


@app.command("/wordle-letters")
def handle_letters(ack, respond, command):
    ack()
    db = Session()
    player = db.query(PlayerSession).filter_by(slack_user_id=command['user_id']).first()

    if not player or player.play_date != date.today():
        db.close()
        respond("you haven't started today's wordle yet! start with `/wordle <guess>`")
        return
    if player.done:
        db.close()
        respond("you already finished... you don't need this tool!")
        return

    green_set = set(player.greens or "")
    yellow_set = set(player.yellows or "")
    gray_set = set(player.grays or "")

    alphabet = set(string.ascii_uppercase)
    used = green_set | yellow_set | gray_set
    missing = alphabet - used

    reply =  f"🟩 {', '.join(sorted(green_set)) or 'None'}\n"
    reply += f"🟨 {', '.join(sorted(yellow_set)) or 'None'}\n"
    reply += f"⬜ {', '.join(sorted(gray_set)) or 'None'}\n"
    reply += f"❔ {', '.join(sorted(missing)) or 'None'}"

    db.close()
    respond(reply)
    return


if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
