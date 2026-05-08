import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from datetime import date
import requests

load_dotenv()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


# load in valid guesses
with open('valid-wordle-words.txt', 'r') as file:
    valid_guesses = {line.strip() for line in file}

# init daily word
today = date.today()

def fetch_word():
    global today
    response = requests.get(f"https://www.nytimes.com/svc/wordle/v2/{today}.json")
    return response.json()["solution"]


daily_word = fetch_word()
print(daily_word)


def check_guess(guess):
    global daily_word

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

    respond(f"{user_guess}: {check_guess(user_guess)}")
    return

@app.command("/wordle-share")
def handle_share(ack, respond, command):
    ack()
    respond("i'm tired boss. no more sharing for you")
    return

if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()