from flask import Flask, request, jsonify
import requests, json
from pyngrok import ngrok

API_TOKEN = ''
MONDAY_API_URL = "https://api.monday.com/v2"
HEADER = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}

app = Flask(__name__)
print(" * ngrok public URL:", ngrok.connect(5000))

def run_query(query, variables=None):
    r = requests.post(MONDAY_API_URL, headers=HEADER, json={"query": query, "variables": variables or {}})
    r.raise_for_status()
    return r.json()

def is_empty(val):
    if val is None: return True
    if isinstance(val, str): return val.strip() == ""
    if isinstance(val, dict):
        # Monday often sends {"label":{"text":"..."}}
        txt = val.get("label", {}).get("text")
        if isinstance(txt, str): return txt.strip() == ""
        return len(val) == 0
    if isinstance(val, (list, tuple, set)): return len(val) == 0
    return False

@app.route('/unassign', methods=['POST'])
def webhook():
    data = request.get_json(force=True) or {}
    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']})

    # assign column can come via query (?assign_column=col_x) or body {"assign_column":"col_x"}
    assign_column_id = request.args.get("assign_column") or data.get("assign_column")
    if not assign_column_id:
        return jsonify({"error": "Missing assign_column"}), 400

    event = data.get("event", {})
    user_id  = event.get("userId")
    item_id  = event.get("pulseId")
    board_id = event.get("boardId")
    value    = event.get("value")

    if not (user_id and item_id and board_id):
        return jsonify({"status": "ignored", "reason": "missing ids"})

    # 🔁 For ALL column changes: assign if value present, unassign if empty
    column_value = {"personsAndTeams": []} if is_empty(value) else {
        "personsAndTeams": [{"id": user_id, "kind": "person"}]
    }

    mutation = """
      mutation ($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
        change_column_value(board_id:$boardId, item_id:$itemId, column_id:$columnId, value:$value){ id }
      }
    """
    vars_ = {
        "boardId": str(board_id),
        "itemId":  str(item_id),
        "columnId": assign_column_id,
        "value":   json.dumps(column_value)
    }

    try:
        res = run_query(mutation, vars_)
        return jsonify({"status": "ok", "result": res})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)

    # POST http://localhost:5000/unassign?assign_column=multiple_person_mkta46k5
