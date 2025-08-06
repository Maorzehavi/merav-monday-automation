from flask import Flask, request, jsonify
import requests
from pyngrok import ngrok
import json

API_TOKEN = ''
COLUMN_ID = "multiple_person_mkta46k5"

HEADER = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

MONDAY_API_URL = "https://api.monday.com/v2"

app = Flask(__name__)

# Expose port 5000 to the public internet
public_url = ngrok.connect(5000)
print(f" * ngrok public URL: {public_url}")

def run_query(query, variables=None):
    data = {'query': query}
    if variables:
        data['variables'] = variables
    response = requests.post(MONDAY_API_URL, headers=HEADER, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(data)

    # Handle challenge response
    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']})

    event = data.get("event", {})
    user_id = event.get("userId")
    item_id = event.get("pulseId")  # Same as item ID
    board_id = event.get("boardId")

    if user_id and item_id and board_id:
        mutation = """
        mutation ($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
          change_column_value(
            board_id: $boardId,
            item_id: $itemId,
            column_id: $columnId,
            value: $value
          ) {
            id
          }
        }
        """

        variables = {
            "boardId": board_id,
            "itemId": item_id,
            "columnId": COLUMN_ID,
            "value": json.dumps({
                "personsAndTeams": [
                    {"id": user_id, "kind": "person"}
                ]
            })
        }

        try:
            result = run_query(mutation, variables)
            print("✅ Assigned user:", result)
        except Exception as e:
            print("❌ Error assigning user:", e)

    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(port=5000)
