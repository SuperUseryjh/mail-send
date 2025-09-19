import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from flask import session, redirect # Import session and redirect from Flask
import os # For generating secret key
import dns.resolver # For MX record lookup

from database import init_db, create_user, get_user_by_username, verify_password, update_user_api_key, generate_api_key, add_domain, get_domains_by_user, update_domain_verification_status

# Initialize the database
init_db()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server # Expose the Flask server for Gunicorn/WSGI

# Set a secret key for session management
# In a production environment, this should be loaded from an environment variable
server.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_for_dev')

# --- MX Record Verification Configuration ---
# Replace with your Postfix server's public IP address or hostname
# This is the value that the user's domain's MX record should point to.
EXPECTED_MX_RECORD_HOST = os.environ.get('EXPECTED_MX_RECORD_HOST', 'your.mailserver.com') 

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# --- Layouts ---
login_layout = dbc.Container([
    dbc.Row(dbc.Col(html.H2("登录", className="text-center my-4"), width=12)),
    dbc.Row(dbc.Col(dbc.Card([
        dbc.CardBody([
            dbc.Form([
                dbc.Label("用户名"),
                dbc.Input(id="login-username", type="text", placeholder="输入用户名", className="mb-3"),
                dbc.Label("密码"),
                dbc.Input(id="login-password", type="password", placeholder="输入密码", className="mb-3"),
                dbc.Button("登录", id="login-button", color="primary", className="me-2"),
                dcc.Link("注册", href="/register", className="btn btn-link")
            ]),
            html.Div(id="login-output", className="mt-3")
        ])
    ]), width=6, lg=4, className="mx-auto"))
], fluid=True)

register_layout = dbc.Container([
    dbc.Row(dbc.Col(html.H2("注册", className="text-center my-4"), width=12)),
    dbc.Row(dbc.Col(dbc.Card([
        dbc.CardBody([
            dbc.Form([
                dbc.Label("用户名"),
                dbc.Input(id="register-username", type="text", placeholder="输入用户名", className="mb-3"),
                dbc.Label("密码"),
                dbc.Input(id="register-password", type="password", placeholder="输入密码", className="mb-3"),
                dbc.Button("注册", id="register-button", color="success", className="me-2"),
                dcc.Link("登录", href="/login", className="btn btn-link")
            ]),
            html.Div(id="register-output", className="mt-3")
        ])
    ]), width=6, lg=4, className="mx-auto"))
], fluid=True)

dashboard_layout = dbc.Container([
    dbc.Row(dbc.Col(html.H2("用户仪表盘", className="text-center my-4"), width=12)),
    dbc.Row(dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H4("欢迎, ", id="welcome-message"),
            html.P("您的 API Key: ", id="api-key-display"),
            dbc.Button("生成新的 API Key", id="generate-api-key-button", color="info", className="mb-3"),
            html.Div(id="api-key-output", className="mt-3"),
            html.Hr(),
            html.H4("域名管理"),
            dbc.Alert([
                html.P("要使用您的域名发送邮件，您需要将域名的 MX 记录指向我们的邮件服务器。请按照以下步骤操作："),
                html.Ol([
                    html.Li(f"登录到您的域名注册商（例如 GoDaddy, Cloudflare, 阿里云等）的 DNS 管理界面。"),
                    html.Li(f"找到您要添加的域名的 DNS 记录设置。"),
                    html.Li(f"添加或修改 MX 记录。以下是您需要配置的详细信息：")
                ]),
                dbc.Table(
                    [
                        html.Thead(html.Tr([html.Th("类型"), html.Th("记录值"), html.Th("优先级"), html.Th("TTL")])),
                        html.Tbody(
                            [
                                html.Tr([html.Td("MX"), html.Td(f"{EXPECTED_MX_RECORD_HOST}"), html.Td("1"), html.Td("Auto")])
                            ]
                        )
                    ],
                    bordered=True, className="mt-3 mb-3"
                ),
                html.Ol([
                    html.Li(f"保存更改。DNS 记录可能需要几分钟到几小时才能在全球范围内生效。"),
                    html.Li(f"在下方输入您的域名并点击 '添加域名'。系统将自动验证 MX 记录。")
                ], start="4") # Start numbering from 4 after the table
            ], color="info", className="mb-3"),
            dbc.Input(id="domain-input", type="text", placeholder="输入要添加的域名", className="mb-3"),
            dbc.Button("添加域名", id="add-domain-button", color="primary", className="me-2"),
            html.Div(id="domain-output", className="mt-3"),
            html.Ul(id="domain-list", className="list-group mt-3"),
            dcc.Link("退出登录", href="/logout", className="btn btn-danger mt-3")
        ])
    ]), width=8, lg=6, className="mx-auto"))
], fluid=True)

# --- Helper Functions ---
def check_mx_record(domain_name):
    """Checks if the domain's MX record points to the expected mail server."""
    try:
        answers = dns.resolver.resolve(domain_name, 'MX')
        for rdata in answers:
            # rdata.exchange is a dns.name.Name object, convert to string
            mx_host = str(rdata.exchange).rstrip('.') # Remove trailing dot
            if mx_host == EXPECTED_MX_RECORD_HOST:
                return True
        return False
    except dns.resolver.NoAnswer:
        return False # No MX record found
    except dns.resolver.NXDOMAIN:
        return False # Domain does not exist
    except Exception as e:
        print(f"Error checking MX record for {domain_name}: {e}")
        return False

# --- Callbacks ---
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/register':
        return register_layout
    elif pathname == '/dashboard':
        if 'user_id' not in session:
            return dcc.Location(pathname="/login", id="redirect-to-login")
        return dashboard_layout
    elif pathname == '/logout':
        session.pop('user_id', None)
        session.pop('username', None)
        return dcc.Location(pathname="/login", id="redirect-to-login")
    else:
        return login_layout

@app.callback(Output('register-output', 'children'),
              [Input('register-button', 'n_clicks')],
              [State('register-username', 'value'),
               State('register-password', 'value')])
def handle_register(n_clicks, username, password):
    if n_clicks:
        if not username or not password:
            return dbc.Alert("用户名和密码不能为空。", color="danger")
        if create_user(username, password):
            return dbc.Alert(f"用户 '{username}' 注册成功！请登录。", color="success")
        else:
            return dbc.Alert(f"用户 '{username}' 已存在。", color="danger")
    return ""

@app.callback(Output('login-output', 'children'),
              [Input('login-button', 'n_clicks')],
              [State('login-username', 'value'),
               State('login-password', 'value')])
def handle_login(n_clicks, username, password):
    if n_clicks:
        if not username or not password:
            return dbc.Alert("用户名和密码不能为空。", color="danger")
        user = get_user_by_username(username)
        if user and verify_password(username, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return dcc.Location(pathname="/dashboard", id="redirect-to-dashboard")
        else:
            return dbc.Alert("用户名或密码错误。", color="danger")
    return ""

@app.callback(
    [Output('welcome-message', 'children'),
     Output('api-key-display', 'children')],
    [Input('url', 'pathname')] # Trigger when URL changes, including initial load of dashboard
)
def update_dashboard_info(pathname):
    if pathname == '/dashboard' and 'user_id' in session:
        user_id = session['user_id']
        username = session['username']
        user = get_user_by_username(username) # Re-fetch user to get latest API key
        if user:
            api_key_display = f"您的 API Key: {user['api_key'] if user['api_key'] else '尚未生成'}"
            return f"欢迎, {username}!", api_key_display
    return dash.no_update, dash.no_update

@app.callback(
    [Output('api-key-output', 'children'),
     Output('api-key-display', 'children', allow_duplicate=True)],
    [Input('generate-api-key-button', 'n_clicks')],
    prevent_initial_call=True
)
def handle_generate_api_key(n_clicks):
    if n_clicks and 'user_id' in session:
        user_id = session['user_id']
        new_api_key = generate_api_key()
        update_user_api_key(user_id, new_api_key)
        return dbc.Alert(f"新�� API Key 已生成: {new_api_key}", color="success"), f"您的 API Key: {new_api_key}"
    return dbc.Alert("无法生成 API Key。请先登录。", color="danger"), dash.no_update

@app.callback(
    Output('domain-output', 'children'),
    [Input('add-domain-button', 'n_clicks')],
    [State('domain-input', 'value')],
    prevent_initial_call=True
)
def handle_add_domain(n_clicks, domain):
    if n_clicks and 'user_id' in session:
        if not domain:
            return dbc.Alert("域名不能为空。", color="danger")
        
        user_id = session['user_id']
        domain_id = add_domain(user_id, domain)
        
        if domain_id is None:
            return dbc.Alert(f"域名 '{domain}' 已存在或添加失败。", color="warning")

        # Perform MX record verification
        is_verified = check_mx_record(domain)
        update_domain_verification_status(domain_id, is_verified)

        if is_verified:
            return dbc.Alert(f"域名 '{domain}' 添加成功并已验证！", color="success")
        else:
            return dbc.Alert(f"域名 '{domain}' 添加成功，但 MX 记录验证失败。请确保 MX 记录指向 {EXPECTED_MX_RECORD_HOST}。", color="warning")
    return dbc.Alert("请先登录以管理域名。", color="danger")

@app.callback(
    Output('domain-list', 'children'),
    [Input('url', 'pathname'),
     Input('add-domain-button', 'n_clicks'), # Trigger refresh when domain is added
     Input('generate-api-key-button', 'n_clicks')], # Also refresh if API key is generated (just for demo)
    prevent_initial_call=True
)
def update_domain_list(pathname, add_clicks, api_key_clicks):
    if pathname == '/dashboard' and 'user_id' in session:
        user_id = session['user_id']
        domains = get_domains_by_user(user_id)
        
        domain_items = []
        if not domains:
            return [dbc.ListGroupItem("尚未添加任何域名。", color="info")]

        for domain in domains:
            status = "已验证" if domain['verified'] else "待验证"
            color = "success" if domain['verified'] else "warning"
            domain_items.append(dbc.ListGroupItem(f"{domain['name']} ({status})", color=color))
        return domain_items
    return []


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)