from app import app
from extensions import socketio

# Disable all Socket.IO event handlers to test basic connection
print("Testing minimal Socket.IO setup...")

if __name__ == "__main__":
    try:
        socketio.run(
            app,
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True  # Allow Werkzeug with SocketIO
        )
    except Exception as e:
        print(f"Socket.IO run failed: {e}")
        print("Falling back to regular Flask server...")
        app.run(host='127.0.0.1', port=5000, debug=False)
