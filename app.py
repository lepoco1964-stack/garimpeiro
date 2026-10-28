import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from googleapiclient.discovery import build

# Configuração da página do App
st.set_page_config(
    page_title="Garimpador Profissional de YouTube",
    page_icon="🚀",
    layout="wide"
)

# Estilização visual limpa e moderna
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    .canal-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Garimpador Profissional de Canais")
st.markdown("Encontre canais promissores em formato de painel visual com fotos, métricas e acesso direto.")

# Abas organizadas
aba1, aba2, aba3 = st.tabs(["⚙️ Configurações & Nicho", "🎯 Canais de Referência", "📊 Painel Visual de Resultados"])

with aba1:
    st.subheader("Parâmetros de Busca")
    chave_api = st.text_input("🔑 Chave da API do YouTube", value="AIzaSyBGrYp-CUjY6ih-cGs8nbtWmXL9bFv-tdE", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        nicho_opcao = st.selectbox(
            "📂 Escolha um Nicho",
            ["Finanças Pessoais", "Histórias / Mistério", "Cortes de Podcast", "Música", "Outro (Digitar abaixo)"]
        )
        if nicho_opcao == "Outro (Digitar abaixo)":
            nicho = st.text_input("🎯 Digite o seu Nicho", value="tecnologia")
        else:
            nicho = nicho_opcao.lower()
            
        max_resultados = st.slider("🔍 Quantos canais buscar", 10, 50, 20, 10)
        
    with col2:
        max_inscritos = st.number_input("👥 Máximo de Inscritos", value=10000, step=1000)
        min_relacao = st.number_input("📈 Relação Mínima (Views / Inscritos)", value=5.0, step=1.0)
        idade_maxima = st.number_input("📅 Idade máxima do canal (Dias)", value=365, step=30)

with aba2:
    st.subheader("Canais de Referência (Opcional)")
    canais_ref_texto = st.text_area("IDs dos Canais (um por linha)", value="", height=150)
    lista_referencias = [c.strip() for c in canais_ref_texto.split("\n") if c.strip()]

with aba3:
    st.subheader("Executar Garimpagem")
    executar_busca = st.button("🔥 INICIAR GARIMPAGEM VISUAL")

# Função de busca melhorada
def pegar_dados_canal(youtube_client, canal_id, origem="Busca automática"):
    try:
        stats = youtube_client.channels().list(
            id=canal_id, part="statistics,snippet"
        ).execute()["items"][0]
        
        nome = stats["snippet"]["title"]
        descricao = stats["snippet"].get("description", "Sem descrição.")
        data_criacao = stats["snippet"]["publishedAt"]
        foto_url = stats["snippet"]["thumbnails"]["high"]["url"]
        
        inscritos = int(stats["statistics"].get("subscriberCount", 0))
        total_visualizacoes = int(stats["statistics"].get("viewCount", 0))
        qtd_videos = int(stats["statistics"].get("videoCount", 0))
        
        media_por_video = total_visualizacoes / qtd_videos if qtd_videos > 0 else 0
        relacao = media_por_video / inscritos if inscritos > 0 else 0
        
        return {
            "foto": foto_url,
            "nome": nome,
            "descricao": descricao[:120] + "...",
            "canal_id": canal_id,
            "inscritos": inscritos,
            "videos": qtd_videos,
            "media_visualizacoes_video": round(media_por_video),
            "relacao_vid_ins": round(relacao, 2),
            "data_criacao": data_criacao[:10],
            "url": f"https://youtube.com/channel/{canal_id}",
            "origem": origem
        }
    except Exception as e:
        return None

if executar_busca:
    if not chave_api:
        st.error("⚠️ Insira a Chave da API.")
    else:
        try:
            youtube = build("youtube", "v3", developerKey=chave_api)
            todos_canais = []
            
            with st.spinner(f"🔍 A garimpar canais de '{nicho}'..."):
                data_limite = (datetime.now() - timedelta(days=idade_maxima)).isoformat() + "Z"
                
                request = youtube.search().list(
                    q=nicho, type="channel", part="id,snippet",
                    maxResults=max_resultados, publishedAfter=data_limite
                )
                response = request.execute()
                
                for item in response.get("items", []):
                    canal_id = item["id"]["channelId"]
                    dados = pegar_dados_canal(youtube, canal_id, origem="Busca automática")
                    if dados and 0 < dados["inscritos"] <= max_inscritos:
                        if dados["relacao_vid_ins"] >= min_relacao:
                            todos_canais.append(dados)
                
                if lista_referencias:
                    for cid in lista_referencias:
                        dados_ref = pegar_dados_canal(youtube, cid, origem="✅ Referência")
                        if dados_ref:
                            todos_canais.append(dados_ref)
            
            if todos_canais:
                st.success(f"🎉 Encontrados {len(todos_canais)} canais promissores!")
                
                # Exibição em Cards Visuais Modernos
                for canal in todos_canais:
                    with st.container():
                        st.markdown(f"""
                        <div class="canal-card">
                            <h3>{canal['nome']} ({canal['origem']})</h3>
                            <p><b>📅 Criado em:</b> {canal['data_criacao']} | <b>👥 Inscritos:</b> {canal['inscritos']:,} | <b>📊 Média Views/Vídeo:</b> {canal['media_visualizacoes_video']:,}</p>
                            <p><i>{canal['descricao']}</i></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_img, col_btn = st.columns([1, 3])
                        with col_img:
                            st.image(canal['foto'], width=120)
                        with col_btn:
                            st.markdown(f"<br>", unsafe_allow_html=True)
                            st.link_button("🔗 Aceder ao Canal no YouTube", canal['url'])
                        st.divider()
                
                # Exportar para Excel
                df = pd.DataFrame(todos_canais)
                nome_arquivo = f"canais-{nicho.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(nome_arquivo, index=False)
                
                with open(nome_arquivo, "rb") as file:
                    st.download_button(
                        label="📥 Descarregar Planilha Excel Completa",
                        data=file,
                        file_name=nome_arquivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("⚠️ Nenhum canal encontrado com estes filtros rigorosos.")
                
        except Exception as e:
            st.error(f"❌ Erro na execução: {e}")
