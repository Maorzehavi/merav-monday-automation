from flask import Flask, request, jsonify
import requests
from pyngrok import ngrok
import json

API_TOKEN = ''  
COLUMN_ID = "multiple_person_mkta46k5"          
CHECK_COLUMN_ID = "color_mkt86f8b"               

HEADER = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

MONDAY_API_URL = "https://api.monday.com/v2"

app = Flask(__name__)


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

    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']})

    event = data.get("event", {})
    user_id = event.get("userId")
    item_id = event.get("pulseId")
    board_id = event.get("boardId")
    column_id = event.get("columnId")
    value = event.get("value", {})
    label = value.get("label", {})
    text = label.get("text", "")

    if column_id == CHECK_COLUMN_ID and user_id and item_id and board_id:
        if text.strip() == "":
            column_value = { "personsAndTeams": [] }
            print("🔄 Unassigning user (empty value)")
        else:
            column_value = {
                "personsAndTeams": [
                    { "id": user_id, "kind": "person" }
                ]
            }
            print(f"👤 Assigning user {user_id}")

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
            "boardId": str(board_id),
            "itemId": str(item_id),
            "columnId": COLUMN_ID,
            "value": json.dumps(column_value)
        }

        try:
            result = run_query(mutation, variables)
            print("✅ Column updated:", result)
        except Exception as e:
            print("❌ Error updating column:", e)
    else:
        print("Skipped: Not target column or missing data")

    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(port=5000)
