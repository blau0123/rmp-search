import os, sys, requests
from flask import Flask, request
from pymessenger import Bot
from bs4 import BeautifulSoup

app = Flask(__name__)

PAGE_ACCESS_TOKEN = "EAAExcaw2oZBkBAGTdwXbRhCMIVUQA0YRY2ZCos5kKdZBunddGrndziu8DyXczC3UZA0r5SPWfUYjAth5Bcul0peMQ1zc5HJF7w6nQz5L01pm1aNAqt391cGVwEX3am5p1pcZACwISrGJrTscgyGTFVq4oZB6MV7WsZBNZCZBZAUu8tCwZDZD"
# PAGE_ACCESS_TOKEN = "EAAfiI73r130BAPnZCzFH6iR5eNpQrCU1DSi8j72T93XSsTUev60oxXH6mbuyZCBSFNXdvrfIBUR5KydZArcBylcm3d5tNAGNzKYBLvzAlJD01EBhLZCiFhHRbs5ZBflelGiqQcDjUB9HID9CdWGKcjlPVEA1ZCYDY7VqJZBjNzwvQZDZD"
VERIFICATION_TOKEN = "litty"
bot = Bot(PAGE_ACCESS_TOKEN)


@app.route('/', methods=['GET'])
# Webhook validation
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFICATION_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Success!", 200


@app.route('/', methods=['POST'])
def webhook():
    # get the data from the user's message
    data = request.get_json()
    log(data)
    data = dict([(str(k), v) for k, v in data.items()])
    # orig url without prof name
    rmp_url = "https://www.ratemyprofessors.com/search.jsp?query="
    final_msg = ""
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                # get id's for sender and recipient
                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']

                if messaging_event.get('message'):
                    if messaging_event['message'].get('text'):
                        # Retrieve the name of the professor (what the user inputs)
                        response = "Prof. " + messaging_event['message']['text'].upper() + "!"
                        final_msg += response + "\n"

                        # get array of each element of professor name (last and first name)
                        input = messaging_event['message']['text'].split()
                        prof_name = ""

                        # concatenate into a professor name
                        for item in input:
                            prof_name += item + " "

                        # add professor name to url to search for professor
                        rmp_url += prof_name

                        # web scraping the search page for the link to the professors page
                        page = requests.get(rmp_url)
                        soup = BeautifulSoup(page.content, 'html.parser')
                        try:
                            prof = soup.findAll('li', {'class': 'listing PROFESSOR'})
                            if len(prof) > 1:
                                # there's multiple profs with that name, send link to search result
                                bot.send_text_message(sender_id, "Multiple professors with that name found!")
                                url_button = [
                                    {
                                        "type": "web_url",
                                        "url": rmp_url,
                                        "title": "RateMyProfessor!",
                                    }
                                ]

                                bot.send_button_message(sender_id, "Here's the search result for " + response,
                                                        url_button)

                            else:
                                # if only one prof, then get that first prof and find its link to the prof's page
                                prof = prof[0].findChild('a', href=True, recursive=False)
                                # concatenate the link to the prof to rmp.com
                                prof_page = "https://www.ratemyprofessors.com" + prof.get('href')

                                page = requests.get(prof_page)
                                soup = BeautifulSoup(page.content, 'html.parser')
                                rating = soup.findAll('div', {'class': 'grade'})
                                # add profs rating, would take again %, and difficulty to final message
                                final_msg += "Rating: " + rating[0].text + "\n"
                                final_msg += "Would take again: " + rating[1].text + "\n"
                                final_msg += "Difficulty: " + rating[2].text + "\n"

                                # find all tags and put into an array then get the first two (top two tags)
                                tags = soup.findAll('span', {'class': 'tag-box-choosetags'})
                                # if there's more than one tag, then show the top two tags
                                if len(tags) > 1:
                                    final_msg += "Top two tags by students:\n" + tags[0].text + "\n" + tags[1].text
                                # if only one tag, show the only tag
                                elif len(tags) == 1:
                                    final_msg += "Only one tag for this professor:\n" + tags[0].text
                                # if there's no tag, then tell the user there's no tag
                                else:
                                    final_msg += "No tags for this professor!\n"

                                # print summary of prof and button to their page
                                bot.send_text_message(sender_id, final_msg)
                                url_button = [
                                    {
                                        "type": "web_url",
                                        "url": prof_page,
                                        "title": "RateMyProfessor!",
                                    }
                                ]
                                bot.send_button_message(sender_id, "Here's the page for " + response, url_button)

                        except:
                            # if there's an error with getting the link, there's no professor
                            bot.send_text_message(sender_id, "No professor found")

    return 'ok', 200


def log(message):
    from pprint import pprint
    pprint(message)
    sys.stdout.flush()


if __name__ == "__main__":
    app.run()