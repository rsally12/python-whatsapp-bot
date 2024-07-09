import logging
from flask import current_app, jsonify, request
import json
import requests
import re

# Temporary storage for user interactions
user_interactions = {}

# Dietary options for the first question
first_question_options = ["Animal Meats",
                          "Added Sugars", "Sodium/Salt", "Saturated Fat"]
# Dietary options for the second question
second_question_options = ["Whole Grains",
                           "Plant Proteins", "Vegetables", "Fruit", "Fish"]


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        log_http_response(response)
        return response


def send_interactive_message_with_buttons(recipient, buttons, text):
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
    headers = {
        "Authorization": "Bearer " + current_app.config['ACCESS_TOKEN'],
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": text
            },
            "action": {
                "buttons": buttons
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Interactive message sent to {recipient}")
        logging.info(response.json())
    except requests.RequestException as e:
        logging.error(f"Failed to send interactive message: {e}")
    return response


# def send_initial_message(recipient):
#     buttons = [
#         {
#             "type": "reply",
#             "reply": {
#                 "id": "animal_meats_button",
#                 "title": "Animal Meats"
#             }
#         },
#         {
#             "type": "reply",
#             "reply": {
#                 "id": "added_sugars_button",
#                 "title": "Added Sugars"
#             }
#         },
#         {
#             "type": "reply",
#             "reply": {
#                 "id": "none_button",
#                 "title": "None"
#             }
#         }
#     ]
#     send_interactive_message_with_buttons(recipient, buttons)

def send_initial_message(recipient):
    buttons = get_next_buttons(recipient, first_question_options)
    text = "We will ask you some questions on your dietary goals. Which of these would you like to get less of?"
    send_interactive_message_with_buttons(recipient, buttons, text)


def send_followup_message(recipient, question_type):
    options = first_question_options if question_type == "first" else second_question_options
    buttons = get_next_buttons(recipient, options)
    text = "Great! Thanks. Please continue to choose your dietary goals from this list. Or select None to move on."
    send_interactive_message_with_buttons(recipient, buttons, text)


def send_second_question_message(recipient):
    buttons = get_next_buttons(recipient, second_question_options)
    text = "Great! Next, tell us which of these you would like to get more of:"
    send_interactive_message_with_buttons(recipient, buttons, text)


def get_next_buttons(wa_id, options):
    user_data = user_interactions[wa_id]
    options_left = [
        opt for opt in options if opt not in user_data["replaced_buttons"]]
    if len(options_left) > 2:
        return [
            {
                "type": "reply",
                "reply": {
                    "id": f"{options_left[0].lower().replace(' ', '_')}_button",
                    "title": options_left[0]
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": f"{options_left[1].lower().replace(' ', '_')}_button",
                    "title": options_left[1]
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "none_button",
                    "title": "None"
                }
            }
        ]
    elif len(options_left) == 1:
        return [
            {
                "type": "reply",
                "reply": {
                    "id": f"{options_left[0].lower().replace(' ', '_')}_button",
                    "title": options_left[0]
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "none_button",
                    "title": "None"
                }
            }
        ]
    return [
        {
            "type": "reply",
            "reply": {
                "id": f"{options_left[0].lower().replace(' ', '_')}_button",
                "title": options_left[0]
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": f"{options_left[1].lower().replace(' ', '_')}_button",
                "title": options_left[1]
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "none_button",
                "title": "None"
            }
        }
    ]


# def process_text_for_whatsapp(text):
#     pattern = r"\【.*?\】"
#     text = re.sub(pattern, "", text).strip()
#     pattern = r"\*\*(.*?)\*\*"
#     replacement = r"*\1*"
#     whatsapp_style_text = re.sub(pattern, replacement, text)
#     return whatsapp_style_text


def update_buttons(wa_id, selected_option):
    user_data = user_interactions[wa_id]
    if user_data["current_screen"] == "FIRST_QUESTION":
        user_data["replaced_buttons"].append(selected_option)
        user_data["first_question_responses"].append(selected_option)
        if len(user_data["replaced_buttons"]) >= len(first_question_options):
            user_data["current_screen"] = "SECOND_QUESTION"
            user_data["replaced_buttons"] = []
            send_second_question_message(wa_id)
        else:
            send_followup_message(wa_id, "first")
    elif user_data["current_screen"] == "SECOND_QUESTION":
        user_data["replaced_buttons"].append(selected_option)
        user_data["second_question_responses"].append(selected_option)
        if len(user_data["replaced_buttons"]) >= len(second_question_options):
            user_data["current_screen"] = "ENTER_LIST_ITEMS"
            prompt_for_list_items(wa_id)
        else:
            send_followup_message(wa_id, "second")


def complete_flow(wa_id):
    responses = user_interactions[wa_id]
    first_responses = ', '.join(responses["first_question_responses"])
    second_responses = ', '.join(responses["second_question_responses"])
    summary = f"Thank you for your responses! Here are your choices:\nLess of: {first_responses}\nMore of: {second_responses}"
    send_whatsapp_message(wa_id, summary)
    logging.info(
        f"User {wa_id} responses:\nLess of: {first_responses}\nMore of: {second_responses}")
    prompt_for_list_items(wa_id)


def send_whatsapp_message(wa_id, text):
    data = get_text_message_input(wa_id, text)
    send_message(data)


def prompt_for_list_items(wa_id):
    text = "Now, please enter the items you want to list, separated by commas."
    send_whatsapp_message(wa_id, text)


def process_text_message(wa_id, text):
    items = [item.strip() for item in text.split(",")]
    user_interactions[wa_id]["list_items"] = items
    items_text = ', '.join(items)
    response_text = f"Thank you! You've entered: {items_text}"
    send_whatsapp_message(wa_id, response_text)
    logging.info(f"User {wa_id} entered list items: {items_text}")


def process_whatsapp_message(body):
    logging.info("Processing incoming WhatsApp message...")
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    if wa_id not in user_interactions:
        user_interactions[wa_id] = {
            "current_screen": "FIRST_QUESTION",
            "responses": {},
            "replaced_buttons": [],
            "first_question_responses": [],
            "second_question_responses": [],
            "list_items": []
        }
        send_initial_message(wa_id)
        return

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    if "interactive" in message:
        user_response_id = message["interactive"]["button_reply"]["id"]
        user_response_title = message["interactive"]["button_reply"]["title"]
        logging.info(f"User clicked button: {user_response_title}")
        current_screen = user_interactions[wa_id]["current_screen"]

        if current_screen in ["FIRST_QUESTION", "SECOND_QUESTION"]:
            if user_response_title in first_question_options + second_question_options:
                update_buttons(wa_id, user_response_title)
            elif user_response_title == "None":
                if current_screen == "FIRST_QUESTION":
                    user_interactions[wa_id]["current_screen"] = "SECOND_QUESTION"
                    user_interactions[wa_id]["replaced_buttons"] = []
                    send_second_question_message(wa_id)
                else:
                    complete_flow(wa_id)
            else:
                send_initial_message(wa_id)
    elif "text" in message:
        user_text = message["text"]["body"]
        logging.info(f"User {wa_id} sent text message: {user_text}")
        if user_interactions[wa_id]["current_screen"] == "ENTER_LIST_ITEMS":
            process_text_message(wa_id, user_text)


def is_valid_whatsapp_message(body):
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )

# Example function stubs for handling other questions


# def handle_question_one(wa_id):
#     text = "Question 1: Choose from the options: Option 1, Option 2, Option 3"
#     data = get_text_message_input(wa_id, text)
#     send_message(data)


# def handle_question_two(wa_id):
#     text = "Question 2: Choose from the options: Option A, Option B, Option C"
#     data = get_text_message_input(wa_id, text)
#     send_message(data)


# def handle_question_three(wa_id):
#     text = "Question 3: Choose from the options: Choice X, Choice Y, Choice Z"
#     data = get_text_message_input(wa_id, text)
#     send_message(data)
