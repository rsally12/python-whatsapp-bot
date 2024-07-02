import logging
from flask import current_app, jsonify, request
import json
import requests
from app.services.openai_service import generate_response
import re

# Temporary storage for user interactions
user_interactions = {}

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    #print(recipient, text)
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def generate_response(response):
    # Return text in uppercase
    print("Hi")
    return response.upper()


def send_message(data):
    #print(data)
    #print(type(data))
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    #print(headers)
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        #print("heeeeyyyyyyyyyyyy")
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response

# Send Welcome Message
'''
def send_welcome_message(recipient):
    welcome_text = "Welcome to our service! How can we assist you today?"
    data = get_text_message_input(recipient, welcome_text)
    send_message(data)
'''    
        
#Send interactive example
'''   
def send_interactive_message_with_buttons(recipient):
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
                "text": "Do you want to proceed?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "yes_button",
                            "title": "Yes"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "idk_button",
                            "title": "IDK"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "no_button",
                            "title": "No"
                        }
                    }
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    print(response.json())
    return response
'''
'''
# Checkbox buttons
def send_checkbox_buttons(recipient):
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
            "type": "list",
            "header": {
                "type": "text",
                "text": "Choose all that apply:"
            },
            "body": {
                "text": "We will ask you some questions on your dietary goals.  Which of these would you like to get less of?"
            },
            "footer": {
                "text": "Select options"
            },
            "action": {
                "button": "Options",
                "sections": [
                    {
                        "title": "Options",
                        "rows": [
                            {"id": "buy_it", "title": "Buy it right away"},
                            {"id": "check_reviews", "title": "Check reviews"},
                            {"id": "share_with_friends", "title": "Share it with"},
                            {"id": "buy_multiple", "title": "Buy multiple,"},
                            {"id": "none", "title": "None of the above"}
                        ]
                    }
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    print(response.json())
    return response
'''
def send_initial_message(recipient):
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
            "type": "list",
            "header": {
                "type": "text",
                "text": "Choose options one by one. Type 'done' when finished."
            },
            "body": {
                "text": "You've found the perfect deal, what do you do next?"
            },
            "footer": {
                "text": "Select options"
            },
            "action": {
                "button": "Options",
                "sections": [
                    {
                        "title": "Options",
                        "rows": [
                            {"id": "buy_it", "title": "Buy it now"},
                            {"id": "check_reviews", "title": "Check reviews"},
                            {"id": "share_with_friends", "title": "Share with friends"},
                            {"id": "buy_multiple", "title": "Buy more"},
                            {"id": "none", "title": "None of the above"}
                        ]
                    }
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    print(response.json())
    return response



def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text

# Temporary storage for user selections
user_selections = {}

def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    print(wa_id)
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    print(name)

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    print(message)

    if message["type"] == "text":
        message_body = message["text"]["body"]
        print(message_body)
        if message_body.lower() == "checkbox":
            send_initial_message(wa_id)
        elif message_body.lower() == "done":
            # Finalize selection
            response = f"You selected: {', '.join(user_selections.get(wa_id, []))}"
            data = get_text_message_input(wa_id, response)
            send_message(data)
            user_selections.pop(wa_id, None)  # Clear selections
        else:
            response = generate_response(message_body)
            data = get_text_message_input(wa_id, response)
            send_message(data)
    elif message["type"] == "interactive":
        interactive_type = message["interactive"]["type"]
        if interactive_type == "list_reply":
            selected_id = message["interactive"]["list_reply"]["id"]
            selected_title = message["interactive"]["list_reply"]["title"]
            print(f"Option selected: {selected_title} (ID: {selected_id})")

            # Store the selection
            if wa_id not in user_selections:
                user_selections[wa_id] = []
            user_selections[wa_id].append(selected_title)

            # Ask the user to select more options or finish
            response = f"You selected: {selected_title}. Select more or type 'done' to finish."
            data = get_text_message_input(wa_id, response)
            send_message(data)
        else:
            print("Unhandled interactive type:", interactive_type)
    else:
        print("Unhandled message type:", message["type"])

'''
def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    print(wa_id)
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    print(name)

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    print(message)

    if message["type"] == "text":
        message_body = message["text"]["body"]
        print(message_body)
        if message_body.lower() == "checkbox":
            send_checkbox_buttons(wa_id)
        else:
            response = generate_response(message_body)
            data = get_text_message_input(wa_id, response)
            send_message(data)
    elif message["type"] == "interactive":
        interactive_type = message["interactive"]["type"]
        if interactive_type == "list_reply":
            selected_id = message["interactive"]["list_reply"]["id"]
            selected_title = message["interactive"]["list_reply"]["title"]
            print(f"Option selected: {selected_title} (ID: {selected_id})")

            response = f"You selected: {selected_title}"
            data = get_text_message_input(wa_id, response)
            send_message(data)
        elif interactive_type == "button_reply":
            button_id = message["interactive"]["button_reply"]["id"]
            button_title = message["interactive"]["button_reply"]["title"]
            print(f"Button clicked: {button_title} (ID: {button_id})")

            if button_id == "yes_button":
                response = "You clicked Yes!"
            elif button_id == "idk_button":
                response = "You clicked IDK!"
            elif button_id == "no_button":
                response = "You clicked No!"
            else:
                response = f"You clicked {button_title}"

            data = get_text_message_input(wa_id, response)
            send_message(data)
        else:
            print("Unhandled interactive type:", interactive_type)
    else:
        print("Unhandled message type:", message["type"])
'''

''' worked for send interactive part
def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    print(wa_id)
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    print(name)
    
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    print(message)

    if message["type"] == "text":
        message_body = message["text"]["body"]
        print(message_body)
        if message_body.lower() == "button":
            send_interactive_message_with_buttons(wa_id)
        else:
            response = generate_response(message_body)
            data = get_text_message_input(wa_id, response)
            send_message(data)
    elif message["type"] == "interactive":
        interactive_type = message["interactive"]["type"]
        if interactive_type == "button_reply":
            button_id = message["interactive"]["button_reply"]["id"]
            button_title = message["interactive"]["button_reply"]["title"]
            print(f"Button clicked: {button_title} (ID: {button_id})")

            if button_id == "yes_button":
                response = "You clicked Yes!"
            elif button_id == "idk_button":
                response = "You clicked IDK!"
            elif button_id == "no_button":
                response = "You clicked No!"
            else:
                response = f"You clicked {button_title}"

            data = get_text_message_input(wa_id, response)
            send_message(data)
        else:
            print("Unhandled interactive type:", interactive_type)
    else:
        print("Unhandled message type:", message["type"])
'''

''' code that worked but created errors when yes or no button was selected

    message_body = message["text"]["body"]
    print(message_body)
    
    # Updated code to process send_interactive_message
    if message_body.lower() == "hi":
        response = send_interactive_message_with_buttons(wa_id)
    else:
        response = generate_response(message_body)
        data = get_text_message_input(wa_id, response)
        send_message(data)

    print(response.status_code)
    print(response.json())
    '''
    # TODO: implement custom function here
    # response = generate_response(message_body)
    # response = 'HI THERE'
    
    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    # data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    # send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )

# Attempt to implement starting message
'''
@current_app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        body = request.json
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
        return "EVENT_RECEIVED", 200
    else:
        return "NOT_FOUND", 404
'''
