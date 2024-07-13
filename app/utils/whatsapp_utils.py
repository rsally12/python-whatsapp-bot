import logging
from flask import current_app, jsonify, request
import json
import requests
import re
#from PIL import Image, ImageDraw, ImageFont
#import io

# Temporary storage for user interactions
user_interactions = {}

# Dietary options for the first question
first_question_options = ["Animal Meats", "Added Sugars", "Sodium/Salt", "Saturated Fat"]
# Dietary options for the second question
second_question_options = ["Whole Grains", "Plant Proteins", "Vegetables", "Fruit", "Fish"]

# Product information
products = [
    {
        "name": "Tyson Tender & Juicy Extra Meaty Fresh Pork Baby Back Ribs, 2.9 - 4.0 lb",
        "image_url": "https://i5.walmartimages.com/seo/Tyson-Tender-Juicy-Extra-Meaty-Fresh-Pork-Baby-Back-Ribs-2-9-4-0-lb_cd1758bf-38b2-4f69-a807-2447bef2baad.ae0ee379ed97fdc1c60a0f2dd7dc6a66.jpeg?odnHeight=180&odnWidth=180&odnBg=FFFFFF",
        "price": 12.72,
        "url": "https://www.walmart.com/ip/Prairie-Fresh-Natural-Fresh-Pork-Back-Ribs-Bone-in-2-4-3-8-lb-19g-of-Protein-per-4-oz-Serving/465183919?athcpid=465183919&athpgid=AthenaItempage&athcgid=null&athznid=si&athieid=v0_eeMTQ3LjA3LDEzMTMuMDYwMDAwMDAwMDAwMiwwLjExNjA3MzE1NTY2NjQxMDM1LDAuNV8&athstid=CS055~CS004&athguid=2QHQlDSDXQuFQzBSG-Pk7x-cawXcZvN2_rWC&athancid=723867836&athposb=0&athena=true"
    },
    {
        "name": "Boneless, Skinless Chicken Breasts, 4.7-6.1 lb Tray",
        "image_url": "https://i5.walmartimages.com/seo/Boneless-Skinless-Chicken-Breasts-4-7-6-1-lb-Tray_4693e429-b926-4913-984c-dd29d4bdd586.780145c264e407b17e86cd4a7106731f.jpeg?odnHeight=180&odnWidth=180&odnBg=FFFFFF",
        "price": 12.18,
        "url": "https://www.walmart.com/ip/Boneless-Skinless-Chicken-Breasts-4-7-6-1-lb-Tray/27935840"
    },
    {
        "name": "King Arthur Baking Company Unbleached Bread Flour, Non-GMO Project Verified, Certified Kosher, 5lb",
        "image_url": "https://i5.walmartimages.com/seo/King-Arthur-Baking-Company-Unbleached-Bread-Flour-Non-GMO-Project-Verified-Certified-Kosher-5lb_66a80131-e677-4380-a968-fdcf4e154da2.1a2fc9a01e709b238190cf75dc465516.png?odnHeight=180&odnWidth=180&odnBg=FFFFFF",
        "price": 5.58,
        "url": "https://www.walmart.com/ip/King-Arthur-Unbleached-Bread-Flour-Non-GMO-Project-Verified-Certified-Kosher-No-Preservatives-5-Pounds/10535108"
    }
]


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

def get_image_message_input(recipient, image_url, caption):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
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


def update_buttons(wa_id, selected_option):
    user_data = user_interactions[wa_id]
    logging.info(f"Updating buttons for user {wa_id}, selected option: {selected_option}")
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
    logging.info(f"User {wa_id} current screen after update: {user_data['current_screen']}")


def complete_flow(wa_id):
    responses = user_interactions[wa_id]
    first_responses = ', '.join(responses["first_question_responses"])
    second_responses = ', '.join(responses["second_question_responses"])
    summary = f"Thank you for your responses! Here are your choices:\nLess of: {first_responses}\nMore of: {second_responses}"
    send_whatsapp_message(wa_id, summary)
    logging.info(f"User {wa_id} responses:\nLess of: {first_responses}\nMore of: {second_responses}")
    user_interactions[wa_id]["current_screen"] = "ENTER_LIST_ITEMS"
    prompt_for_list_items(wa_id)


def send_whatsapp_message(wa_id, text):
    data = get_text_message_input(wa_id, text)
    send_message(data)

def send_product_messages(wa_id):
    for product in products:
        # Send the product image
        caption = f"{product['name']}\nPrice: ${product['price']}"
        data = get_image_message_input(wa_id, product["image_url"], caption)
        send_message(data)
        
        # Send the Walmart URL as a text message
        url_message = f"View this product on Walmart: {product['url']}"
        data = get_text_message_input(wa_id, url_message)
        send_message(data)

def prompt_for_list_items(wa_id):
    text = "Now, please enter the items you want to list, separated by commas."
    send_whatsapp_message(wa_id, text)


def process_text_message(wa_id, text):
    logging.info(f"Processing text message for {wa_id}")
    items = [item.strip() for item in text.split(",")]
    user_interactions[wa_id]["list_items"] = items
    items_text = ', '.join(items)
    response_text = f"Thank you! You've entered: {items_text}"
    send_whatsapp_message(wa_id, response_text)
    logging.info(f"User {wa_id} entered list items: {items_text}")
    send_product_messages(wa_id)  # Call the function to send product images


def process_whatsapp_message(body):
    logging.info("Processing incoming WhatsApp message...")
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    logging.info(f"WA ID: {wa_id}")
    if wa_id not in user_interactions:
        logging.info(f"New user: {wa_id}")
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
    logging.info(f"Received message: {message}")

    if "interactive" in message:
        user_response_id = message["interactive"]["button_reply"]["id"]
        user_response_title = message["interactive"]["button_reply"]["title"]
        logging.info(f"User clicked button: {user_response_title}")
        current_screen = user_interactions[wa_id]["current_screen"]
        logging.info(f"Current screen: {current_screen}")

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
        current_screen = user_interactions[wa_id]["current_screen"]
        logging.info(f"Current screen: {current_screen}")
        if current_screen == "ENTER_LIST_ITEMS":
            process_text_message(wa_id, user_text)
        else:
            logging.warning(f"Unexpected text message at screen: {current_screen}")


def is_valid_whatsapp_message(body):
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )