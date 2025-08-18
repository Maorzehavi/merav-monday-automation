from flask import Flask, request, jsonify
import requests, json, os

API_TOKEN = os.getenv("API_TOKEN", "")
COLUMN_ID = "multiple_person_mkta46k5"
CHECK_COLUMN_ID = "color_mkt86f8b"

HEADER = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
MONDAY_API_URL = "https://api.monday.com/v2"

app = Flask(__name__)

def run_query(query, variables=None):
    data = {'query': query}
    if variables: data['variables'] = variables
    r = requests.post(MONDAY_API_URL, headers=HEADER, json=data)
    if r.status_code == 200: return r.json()
    raise Exception(f"Query failed {r.status_code}: {r.text}")
    
@app.route('/health')
def health():
    return jsonify({'health': 'ok'})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']})

    event = data.get("event", {})
    user_id = event.get("userId")
    item_id = event.get("pulseId")
    board_id = event.get("boardId")
    column_id = event.get("columnId")
    text = (event.get("value", {}).get("label", {}) or {}).get("text", "")

    if column_id == CHECK_COLUMN_ID and user_id and item_id and board_id:
        column_value = {"personsAndTeams": []} if not text.strip() else {
            "personsAndTeams": [{"id": user_id, "kind": "person"}]
        }

        mutation = """
        mutation ($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
          change_column_value(board_id:$boardId,item_id:$itemId,column_id:$columnId,value:$value){ id }
        }"""
        vars = {
            "boardId": str(board_id),
            "itemId": str(item_id),
            "columnId": COLUMN_ID,
            "value": json.dumps(column_value)
        }
        try:
            result = run_query(mutation, vars)
            print("✅ Column updated:", result)
        except Exception as e:
            print("❌ Error updating column:", e)
    else:
        print("Skipped: Not target column or missing data")

    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
