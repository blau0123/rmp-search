import os, sys, requests
import traceback
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

    final_msg = ""
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                # get id's for sender and recipient
                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']

                if messaging_event.get('message'):
                    if messaging_event['message'].get('text'):
                        try:
                            profs_names = messaging_event['message']['text'].upper()
                            message = messaging_event['message']['text'].upper().split()

                            # if user wants to compare two profs
                            if message[0] == "COMPARE":
                                # should be two elements: COMPARE and the two profs names separated by a comma
                                if len(message) < 2:
                                    bot.send_text_message(sender_id, "Need to enter in format: COMPARE [prof1],[prof2]")
                                else:
                                    # get the prof's names by substringing the COMPARE out of the string and splitting
                                    profs_names = profs_names[len(message[0]) + 1:]
                                    both_profs = profs_names.split(',')
                                    # if two professors, then create them
                                    if len(both_profs) < 2 or len(both_profs) > 4:
                                        bot.send_text_message(sender_id,
                                                              "Need to enter in format: COMPARE [prof1],[prof2]")
                                    else:
                                        # get individual names of the profs
                                        prof_one = both_profs[0]
                                        prof_two = both_profs[1]
                                        final_msg += "COMPARING " + prof_one + " AND " + prof_two + "\n"
                                        # bot.send_text_message(sender_id, final_msg)

                                        # get url for each prof's search page
                                        splitted_one = prof_one.split()
                                        splitted_two = prof_two.split()
                                        first_prof_url = get_prof_url(splitted_one)
                                        second_prof_url = get_prof_url(splitted_two)

                                        # print(first_prof_url)

                                        # web scraping the search page for the link to the professors page
                                        first_prof_search_page = requests.get(first_prof_url)
                                        second_prof_search_page = requests.get(second_prof_url)

                                        # get the soup for each professor's search page
                                        soup_one = BeautifulSoup(first_prof_search_page.content, 'html.parser')
                                        soup_two = BeautifulSoup(second_prof_search_page.content, 'html.parser')

                                        # get list of professors with the inputted name for each prof name
                                        first_prof = soup_one.findAll('li', {'class': 'listing PROFESSOR'})
                                        second_prof = soup_two.findAll('li', {'class': 'listing PROFESSOR'})

                                        # if either of the profs have multiple professors with the name
                                        if len(first_prof) > 1 or len(second_prof) > 1:
                                            # there's multiple profs with that name, send link to search result
                                            if len(first_prof) > 1:
                                                bot.send_text_message(sender_id,
                                                                      "Multiple professors with the name " + prof_one
                                                                      + " found!")
                                            if len(second_prof) > 1:
                                                bot.send_text_message(sender_id,
                                                                      "Multiple professors with the name " + prof_two
                                                                      + " found!")
                                        else:
                                            first_prof_info = get_prof_info(soup_one, first_prof)
                                            second_prof_info = get_prof_info(soup_two, second_prof)

                                            # add each prof's info to the final message
                                            final_msg += str(prof_one) + " rating: " + first_prof_info[1] + "\n"
                                            final_msg += str(prof_two) + " rating: " + second_prof_info[1] + "\n"

                                            final_msg += str(prof_one) + " would take again: " + first_prof_info[
                                                2] + "\n"
                                            final_msg += str(prof_two) + " would take again: " + second_prof_info[
                                                2] + "\n"

                                            final_msg += str(prof_one) + " difficulty: " + first_prof_info[3] + "\n"
                                            final_msg += str(prof_one) + " difficulty: " + second_prof_info[3] + "\n"

                                            # print summary of prof and button to their page
                                            bot.send_text_message(sender_id, final_msg)
                                            url_button = [
                                                {
                                                    "type": "web_url",
                                                    "url": first_prof_info[0],
                                                    "title": "RateMyProfessor!",
                                                }
                                            ]
                                            bot.send_button_message(sender_id, "Here's the page for " + str(prof_one),
                                                                    url_button)

                                            url_button = [
                                                {
                                                    "type": "web_url",
                                                    "url": second_prof_info[0],
                                                    "title": "RateMyProfessor!",
                                                }
                                            ]
                                            bot.send_button_message(sender_id, "Here's the page for " + str(prof_two),
                                                                    url_button)

                            # if the user only typed a prof name
                            else:
                                # Retrieve the name of the professor (what the user inputs)
                                response = "Prof. " + messaging_event['message']['text'].upper() + "!"
                                final_msg += response + "\n"

                                # get url of prof's rmp page
                                # get array of each element of professor name (last and first name)
                                input = messaging_event['message']['text'].split()
                                rmp_url = get_prof_url(input)

                                # web scraping the search page for the link to the professors page
                                page = requests.get(rmp_url)
                                soup = BeautifulSoup(page.content, 'html.parser')
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
                                    # if only with one prof, then get the info for that prof
                                    prof_info = get_prof_info(soup, prof)
                                    final_msg += "Rating: " + prof_info[1] + "\n"
                                    final_msg += "Would take again: " + prof_info[2] + "\n"
                                    final_msg += "Difficulty: " + prof_info[3] + "\n"

                                    top_tags = prof_info[4]
                                    if len(top_tags) > 1:
                                        final_msg += "Top two tags are: " + top_tags[0] + "\n" + top_tags[1]
                                    elif len(top_tags) == 1:
                                        final_msg += "Only one tag for this professor: " + top_tags[0]
                                    else:
                                        final_msg += "No tags for this professor"
                                    # print summary of prof and button to their page
                                    bot.send_text_message(sender_id, final_msg)
                                    url_button = [
                                        {
                                            "type": "web_url",
                                            "url": prof_info[0],
                                            "title": "RateMyProfessor!",
                                        }
                                    ]
                                    bot.send_button_message(sender_id, "Here's the page for " + response, url_button)

                        except Exception as e:
                            traceback.print_exc()
                            # if there's an error with getting the link, there's no professor
                            bot.send_text_message(sender_id, "No professor found")

    return 'ok', 200


def get_prof_url(prof_orig_name):
    # orig url without prof name
    rmp_url = "https://www.ratemyprofessors.com/search.jsp?query="
    prof_name = ""

    # concatenate into a professor name
    for item in prof_orig_name:
        prof_name += item + " "

        # add professor name to url to search for professor
        rmp_url += prof_name

    return rmp_url


def get_prof_info(soup, prof):
    # url of prof page, rating, would take again, difficulty, list of tags
    final_msg = []
    # prof = soup.findAll('li', {'class': 'listing PROFESSOR'})

    # if only one prof, then get that first prof and find its link to the prof's page
    # print(len(prof))
    prof = prof[0].findChild('a', href=True, recursive=False)
    # concatenate the link to the prof to rmp.com
    prof_page = "https://www.ratemyprofessors.com" + prof.get('href')

    page = requests.get(prof_page)
    soup = BeautifulSoup(page.content, 'html.parser')
    rating = soup.findAll('div', {'class': 'grade'})
    # add profs rating, would take again %, and difficulty to final message
    final_msg.append(prof_page)
    final_msg.append(rating[0].text)
    final_msg.append(rating[1].text)
    final_msg.append(rating[2].text)

    # find all tags and put into an array then get the first two (top two tags)
    tags = soup.findAll('span', {'class': 'tag-box-choosetags'})
    list_of_tags = []
    # if there's more than one tag, then show the top two tags
    if len(tags) > 1:
        list_of_tags.append(tags[0].text)
        list_of_tags.append(tags[1].text)
    # if only one tag, show the only tag
    elif len(tags) == 1:
        list_of_tags.append(tags[0].text)
    # if there's no tag, then list_of_tags is empty

    final_msg.append(list_of_tags)
    return final_msg


def log(message):
    from pprint import pprint
    pprint(message)
    sys.stdout.flush()


if __name__ == "__main__":
    app.run()