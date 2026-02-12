import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(
    page_title="Monitor Caixa D'água",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    h1 {
        color: #0f172a;
        font-weight: 700;
    }
    .alert-success {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
    }
    .alert-warning {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
    }
    .alert-danger {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Credenciais de login
USERS = {
    'admin': 'Marl@1890',
    'usuario': 'senha123',
    'monitor': 'monitor2024'
}

API_URL = 'https://script.google.com/macros/s/AKfycbx7kaNvASekDf5duusiRwjq163R9KDs6NEuTqlieUW3f_7hPJo3MhWIS8NURT_tA04/exec'

# Inicializar session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# Função de login
def login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False

# Função de logout
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

# Carregar dados da API
@st.cache_data(ttl=300)
def load_data():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success') and result.get('data'):
            return result['data']
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Formatar tempo
def format_time(minutes):
    if minutes < 60:
        return f"{int(minutes)} min"
    elif minutes < 1440:
        hours = int(minutes / 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}min" if mins > 0 else f"{hours}h"
    else:
        days = int(minutes / 1440)
        hours = int((minutes % 1440) / 60)
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"

# Calcular estatísticas de tempo
def calculate_timing_stats(data):
    if len(data) < 2:
        return "--", "--"
    
    levels = [d['level'] for d in data]
    min_level = min(levels)
    max_level = max(levels)
    
    last_min_index = -1
    last_max_index = -1
    
    for i in range(len(data) - 1, -1, -1):
        if last_min_index == -1 and data[i]['level'] <= min_level + 5:
            last_min_index = i
        if last_max_index == -1 and data[i]['level'] >= max_level - 5:
            last_max_index = i
        if last_min_index != -1 and last_max_index != -1:
            break
    
    fill_time = "--"
    empty_time = "--"
    
    if last_min_index != -1 and last_max_index != -1 and last_max_index > last_min_index:
        min_time = datetime.fromisoformat(data[last_min_index]['dateTime'].replace('Z', '+00:00'))
        max_time = datetime.fromisoformat(data[last_max_index]['dateTime'].replace('Z', '+00:00'))
        time_diff = (max_time - min_time).total_seconds() / 60
        fill_time = format_time(time_diff)
    
    if last_min_index != -1 and last_max_index != -1 and last_min_index > last_max_index:
        max_time = datetime.fromisoformat(data[last_max_index]['dateTime'].replace('Z', '+00:00'))
        min_time = datetime.fromisoformat(data[last_min_index]['dateTime'].replace('Z', '+00:00'))
        time_diff = (min_time - max_time).total_seconds() / 60
        empty_time = format_time(time_diff)
    
    return fill_time, empty_time

# Tela de Login
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>💧 Monitor Caixa D'água</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Acesso restrito - Digite suas credenciais</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("🔐 Entrar", use_container_width=True)
            
            if submit:
                if login(username, password):
                    st.success("Login realizado com sucesso! ✓")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")
        
        st.info("**Credenciais padrão:**\n\nUsuário: `admin` | Senha: `Marl@1890`")

# Dashboard (após login)
else:
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("💧 Monitor Caixa D'água")
    with col2:
        if st.button("🚪 Sair", use_container_width=True):
            logout()
    
    st.markdown(f"**Usuário:** {st.session_state.username}")
    st.divider()
    
    # Carregar dados
    data = load_data()
    
    if data is None or len(data) == 0:
        st.error("❌ Erro ao carregar dados ou nenhum dado disponível.")
        st.stop()
    
    # Dados atuais
    latest = data[-1]
    current_level = latest['level']
    
    # Calcular tempo desde última atualização
    last_update = datetime.fromisoformat(latest['dateTime'].replace('Z', '+00:00'))
    now = datetime.now(last_update.tzinfo)
    diff_minutes = int((now - last_update).total_seconds() / 60)
    update_text = "Agora mesmo" if diff_minutes < 1 else f"Há {diff_minutes} min"
    
    # Alert Banner
    if current_level <= 25:
        st.markdown(f"""
        <div class="alert-danger">
            <strong>⚠️ Nível Crítico!</strong> Apenas {current_level}% de água restante.
        </div>
        """, unsafe_allow_html=True)
    elif current_level <= 50:
        st.markdown(f"""
        <div class="alert-warning">
            <strong>⚡ Atenção!</strong> Nível baixo detectado ({current_level}%).
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-success">
            <strong>✓ Tudo OK!</strong> Nível adequado de água ({current_level}%).
        </div>
        """, unsafe_allow_html=True)
    
    # Métricas principais
    fill_time, empty_time = calculate_timing_stats(data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💧 Nível Atual",
            value=f"{current_level}%",
            delta="Capacidade da caixa"
        )
    
    with col2:
        st.metric(
            label="⏱️ Tempo p/ Encher",
            value=fill_time,
            delta="Estimativa baseada no histórico"
        )
    
    with col3:
        st.metric(
            label="⏳ Tempo p/ Esvaziar",
            value=empty_time,
            delta="Duração estimada"
        )
    
    st.divider()
    
    # Grid principal
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Visualização do Tanque")
        
        # Criar gráfico de gauge para o tanque
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=current_level,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Nível da Caixa", 'font': {'size': 24}},
            number={'suffix': "%", 'font': {'size': 40}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#3b82f6"},
                'bar': {'color': "#3b82f6"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#3b82f6",
                'steps': [
                    {'range': [0, 25], 'color': '#fee2e2'},
                    {'range': [25, 50], 'color': '#fef3c7'},
                    {'range': [50, 100], 'color': '#d1fae5'}
                ],
                'threshold': {
                    'line': {'color': "#ef4444", 'width': 4},
                    'thickness': 0.75,
                    'value': 25
                }
            }
        ))
        
        fig_gauge.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "#0f172a", 'family': "Arial"}
        )
        
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        st.subheader("📊 Histórico (Últimas leituras)")
        
        # Preparar dados para gráfico
        recent_data = data[-10:]  # Últimas 10 leituras
        df = pd.DataFrame(recent_data)
        df['dateTime'] = pd.to_datetime(df['dateTime'])
        df['formatted_time'] = df['dateTime'].dt.strftime('%d/%m %H:%M')
        
        # Criar gráfico de linha
        fig_line = go.Figure()
        
        fig_line.add_trace(go.Scatter(
            x=df['formatted_time'],
            y=df['level'],
            mode='lines+markers',
            name='Nível (%)',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#3b82f6'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        
        fig_line.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Data/Hora",
            yaxis_title="Nível (%)",
            yaxis=dict(range=[0, 100]),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "#0f172a"}
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    
    st.divider()
    
    # Cards de informação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🕐 Última Atualização",
            value=update_text,
            delta="Atualização automática"
        )
    
    with col2:
        st.metric(
            label="💻 Status do Sistema",
            value="✓ Online",
            delta="Operacional"
        )
    
    with col3:
        # Calcular tendência
        if len(data) >= 2:
            previous = data[-2]
            diff = current_level - previous['level']
            
            if diff > 0:
                trend = "Enchendo"
                delta = f"↑ {abs(diff):.1f}%"
            elif diff < 0:
                trend = "Esvaziando"
                delta = f"↓ {abs(diff):.1f}%"
            else:
                trend = "Estável"
                delta = None
        else:
            trend = "--"
            delta = None
        
        st.metric(
            label="📈 Tendência",
            value=trend,
            delta=delta
        )
    
    # Auto-refresh
    st.markdown("---")
    st.info("🔄 Página atualiza automaticamente a cada 5 minutos")
    time.sleep(300)
    st.rerun()
