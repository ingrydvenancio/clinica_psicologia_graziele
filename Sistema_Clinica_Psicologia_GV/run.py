import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Compatível com Windows e Linux
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
