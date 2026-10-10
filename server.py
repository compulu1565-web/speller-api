import json
import os
import re
import urllib.parse
import urllib.request

from flask import Flask, jsonify, request

app = Flask(__name__)

SPELLER_URL = "https://nara-speller.co.kr/old_speller/results"


@app.get("/")
def home():
    return "Speller API (Python)"


@app.post("/")
def spell_check():
    body = request.get_json(silent=True)

    if not body or not isinstance(body.get("text"), str):
        return "Invalid request body", 400

    text = body["text"].replace("\n", "\r\n")

    try:
        encoded = urllib.parse.urlencode({
            "text1": text
        }).encode("utf-8")

        req = urllib.request.Request(
            SPELLER_URL,
            data=encoded,
            method="POST",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
            },
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")

        match = re.search(
            r"data\s*=\s*(\[.*?\]);",
            html,
            flags=re.DOTALL,
        )

        if not match:
            print("Could not find data payload")
            print(html[:1000])

            return jsonify({
                "suggestions": []
            })

        parsed = json.loads(match.group(1))

        if not parsed:
            return jsonify({
                "suggestions": []
            })

        data = parsed[0]

        if isinstance(data, list):
            if not data:
                err_info = []
            else:
                data = data[0]
                err_info = data.get("errInfo", [])
        else:
            err_info = data.get("errInfo", [])

        suggestions = []

        for err in err_info:
            candidate = err.get("candWord")

            if not candidate:
                continue

            suggestions.append({
                "description": err.get("help", ""),
                "start": err.get("start", 0),
                "end": err.get("end", 0),
                "text": err.get("orgStr", ""),
                "candidates": candidate.split("|"),
            })

        return jsonify({
            "suggestions": suggestions
        })

    except Exception as e:
        print("SPELL CHECK ERROR:", repr(e))

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))

    app.run(
        host="0.0.0.0",
        port=port
    )
