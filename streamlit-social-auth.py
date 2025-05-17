import streamlit as st
import yaml
from yaml.loader import SafeLoader
import bcrypt
import jwt
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import requests
import os
import uuid
from authlib.integrations.requests_client import OAuth2Session
from urllib.parse import urlencode
import json

class SocialAuthenticator:
    """
    This class creates a social authentication module that can be used to create a login widget
    allowing users to authenticate using social logins like Google, Microsoft, Procore, etc.,
    alongside traditional username/password authentication.
    """
    
    def __init__(self, config_path=None, config_data=None, cookie_name='socialauth_cookie',
                 key='socialauth_key', cookie_expiry_days=30, ssl_enabled=False):
        """
        Initialize the SocialAuthenticator with given parameters.
        """
        self.cookie_name = cookie_name
        self.key = key
        self.cookie_expiry_days = cookie_expiry_days
        self.ssl_enabled = ssl_enabled
        self.cookie_manager = stx.CookieManager()
        
        # Load config
        if config_path:
            with open(config_path) as file:
                self.config = yaml.load(file, Loader=SafeLoader)
        elif config_data:
            self.config = config_data
        else:
            raise ValueError("Either config_path or config_data must be provided.")
        
        # Initialize JWT token secret
        self.jwt_secret = self.config.get('jwt_secret', os.urandom(32).hex())
        
        # Initialize social login credentials
        self.social_providers = self.config.get('social_providers', {})
        
        # Save redirect URI for later use
        self.redirect_uri = self.config.get('redirect_uri', 'http://localhost:8501')
        
        # Initialize credentials
        self.credentials = self.config.get('credentials', {})
    
    def _token_encode(self, username, source, expiry=None):
        """
        Encodes the contents of the token.
        """
        if expiry is None:
            expiry = datetime.utcnow() + timedelta(days=self.cookie_expiry_days)
            
        payload = {
            'exp': expiry,
            'sub': username,
            'src': source,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def _token_decode(self, token):
        """
        Decodes the token contents.
        """
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
        except:
            return False
    
    def _check_pw(self, username, password):
        """
        Checks if the password entered matches the one in the config file.
        """
        if not self.credentials.get('usernames') or username not in self.credentials['usernames']:
            return False
        
        user_pw = self.credentials['usernames'][username]['password']
        return bcrypt.checkpw(password.encode(), user_pw.encode())
    
    def _check_cookie(self):
        """
        Checks if the cookie exists and validates it.
        """
        token = self.cookie_manager.get(self.cookie_name)
        if token is not None:
            decoded_token = self._token_decode(token)
            if decoded_token:
                return decoded_token['sub'], decoded_token['src']
        return False, None
    
    def _set_cookie(self, username, source):
        """
        Sets the auth cookie with encoded token.
        """
        token = self._token_encode(username, source)
        self.cookie_manager.set(
            self.cookie_name,
            token,
            expires_at=datetime.now() + timedelta(days=self.cookie_expiry_days),
            secure=self.ssl_enabled
        )
    
    def _auth_state_callback(self):
        """
        Callback for OAuth state validation.
        """
        if 'oauth_state' in st.session_state:
            return st.session_state['oauth_state']
        state = str(uuid.uuid4())
        st.session_state['oauth_state'] = state
        return state
    
    def _get_oauth_session(self, provider):
        """
        Creates an OAuth2 session for the given provider.
        """
        if provider not in self.social_providers:
            raise ValueError(f"Provider {provider} not configured")
        
        provider_config = self.social_providers[provider]
        
        return OAuth2Session(
            provider_config['client_id'],
            provider_config['client_secret'],
            scope=provider_config.get('scope', ''),
            redirect_uri=self.redirect_uri
        )
    
    def _get_auth_url(self, provider):
        """
        Gets the authorization URL for the given provider.
        """
        if provider not in self.social_providers:
            raise ValueError(f"Provider {provider} not configured")
        
        provider_config = self.social_providers[provider]
        state = self._auth_state_callback()
        
        params = {
            'client_id': provider_config['client_id'],
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': provider_config.get('scope', '')
        }
        
        return f"{provider_config['auth_url']}?{urlencode(params)}"
    
    def _handle_callback(self, provider, code, state):
        """
        Handles the OAuth callback and exchanges code for tokens.
        """
        if provider not in self.social_providers:
            raise ValueError(f"Provider {provider} not configured")
        
        # Verify state
        if state != st.session_state.get('oauth_state'):
            return None
        
        provider_config = self.social_providers[provider]
        
        # Exchange code for token
        token_params = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': provider_config['client_id'],
            'client_secret': provider_config['client_secret']
        }
        
        response = requests.post(provider_config['token_url'], data=token_params)
        
        if response.status_code != 200:
            return None
        
        token_data = response.json()
        
        # Get user info
        user_info_response = requests.get(
            provider_config['userinfo_url'],
            headers={'Authorization': f"Bearer {token_data['access_token']}"}
        )
        
        if user_info_response.status_code != 200:
            return None
        
        return user_info_response.json()
    
    def _extract_user_identifier(self, provider, user_info):
        """
        Extracts username/email from provider-specific user info.
        """
        if provider not in self.social_providers:
            raise ValueError(f"Provider {provider} not configured")
        
        provider_config = self.social_providers[provider]
        id_field = provider_config.get('id_field', 'email')
        
        # Handle nested fields with dot notation
        if '.' in id_field:
            parts = id_field.split('.')
            value = user_info
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return None
            return value
        
        return user_info.get(id_field)
    
    def login(self, form_name="Login", location='main', social_buttons=True):
        """
        Creates a login widget.
        """
        # Check if the user is already authenticated
        username, source = self._check_cookie()
        if username:
            return True, username, source
        
        # Get query parameters
        query_params = st.experimental_get_query_params()
        
        # Check if this is an OAuth callback
        if 'code' in query_params and 'state' in query_params and 'provider' in query_params:
            provider = query_params['provider'][0]
            code = query_params['code'][0]
            state = query_params['state'][0]
            
            user_info = self._handle_callback(provider, code, state)
            
            if user_info:
                user_id = self._extract_user_identifier(provider, user_info)
                
                if user_id:
                    self._set_cookie(user_id, provider)
                    # Clear query parameters to avoid repeated processing
                    st.experimental_set_query_params()
                    st.rerun()
                    return True, user_id, provider
        
        # Not authenticated, show login form
        if location == 'sidebar':
            login_form = st.sidebar.form(form_name)
        else:
            login_form = st.form(form_name)
        
        with login_form:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if self._check_pw(username, password):
                    self._set_cookie(username, 'local')
                    return True, username, 'local'
                else:
                    st.error("Invalid username or password")
        
        # Social login buttons
        if social_buttons:
            st.write("Or login with:")
            
            cols = st.columns(len(self.social_providers))
            
            for i, (provider, config) in enumerate(self.social_providers.items()):
                with cols[i]:
                    if st.button(f"{provider.capitalize()}"):
                        auth_url = self._get_auth_url(provider)
                        # Store provider in query params for callback
                        st.experimental_set_query_params(provider=provider)
                        # Redirect to authorization URL
                        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{auth_url}\'">', unsafe_allow_html=True)
                        return False, None, None
        
        return False, None, None
    
    def logout(self):
        """
        Logs out the user.
        """
        self.cookie_manager.delete(self.cookie_name)
        return True


# Example configuration YAML structure:
"""
credentials:
  usernames:
    johndoe:
      email: johndoe@gmail.com
      name: John Doe
      password: $2b$12$tPaJoUQp9s7KdAF.KGyFlOANZK/ClQiSdl9Bha1JGl6iBloxOGhA.  # hashed password
    janedoe:
      email: janedoe@gmail.com
      name: Jane Doe
      password: $2b$12$tPaJoUQp9s7KdAF.KGyFlOANZK/ClQiSdl9Bha1JGl6iBloxOGhA.  # hashed password

jwt_secret: your_jwt_secret_here
redirect_uri: http://localhost:8501

social_providers:
  google:
    client_id: your_google_client_id
    client_secret: your_google_client_secret
    auth_url: https://accounts.google.com/o/oauth2/auth
    token_url: https://oauth2.googleapis.com/token
    userinfo_url: https://www.googleapis.com/oauth2/v3/userinfo
    scope: openid email profile
    id_field: email

  microsoft:
    client_id: your_microsoft_client_id
    client_secret: your_microsoft_client_secret
    auth_url: https://login.microsoftonline.com/common/oauth2/v2.0/authorize
    token_url: https://login.microsoftonline.com/common/oauth2/v2.0/token
    userinfo_url: https://graph.microsoft.com/v1.0/me
    scope: openid email profile User.Read
    id_field: userPrincipalName

  procore:
    client_id: your_procore_client_id
    client_secret: your_procore_client_secret
    auth_url: https://login.procore.com/oauth/authorize
    token_url: https://login.procore.com/oauth/token
    userinfo_url: https://api.procore.com/rest/v1.0/me
    scope: openid email profile
    id_field: email
"""

# Example usage:
"""
import streamlit as st
import yaml
from social_authenticator import SocialAuthenticator

# Initialize the authenticator
authenticator = SocialAuthenticator('config.yaml')

# Create a login widget
authenticated, username, auth_source = authenticator.login()

# Check if the user is authenticated
if authenticated:
    st.write(f"Welcome {username}! You are logged in via {auth_source}.")
    
    # Add a logout button
    if st.button("Logout"):
        authenticator.logout()
        st.rerun()
else:
    st.warning("Please login to continue.")
"""