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

# Estilização visual com abas coloridas e botões personalizados
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
    .stButton button {
        background-color: #00C853 !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Garimpador de Canais do YouTube")
st.markdown("Encontre canais promissores e em alta através de um painel interativo.")

# Abas coloridas e organizadas
aba1, aba2, aba3 = st.tabs(["⚙️ Configurações & Nicho", "🎯 Canais de Referência", "📊 Resultados & Exportação"])

with aba1:
    st.subheader("Parâmetros e Escolha do Nicho")
    
    # Chave da API pré-configurada ou campo para inserir
    chave_api = st.text_input("🔑 Chave da API do YouTube", value="AIzaSyBGrYp-CUjY6ih-cGs8nbtWmXL9bFv-tdE", type="password")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Caixa de seleção rápida de nichos populares + opção personalizada
        nicho_opcao = st.selectbox(
            "📂 Escolha um Nicho em Alta",
            ["Finanças Pessoais", "Histórias / Mistério", "Cortes de Podcast", "Música", "Outro (Digitar abaixo)"]
        )
        
        if nicho_opcao == "Outro (Digitar abaixo)":
            nicho = st.text_input("🎯 Digite o seu Nicho / Palavra-chave", value="tecnologia")
        else:
            nicho = nicho_opcao.lower()
            
        max_resultados = st.slider("🔍 Quantos canais buscar", 10, 100, 50, 10)
        
    with col2:
        max_inscritos = st.number_input("👥 Máximo de Inscritos", value=5000, step=500)
        min_relacao = st.number_input("📈 Relação Mínima (Views / Inscritos)", value=10.0, step=1.0)
        idade_maxima = st.number_input("📅 Idade máxima do canal (Dias)", value=180, step=30)

with aba2:
    st.subheader("Canais de Referência (Opcional)")
    st.markdown("Cole abaixo os IDs dos canais de referência (um por linha):")
    
    canais_ref_texto = st.text_area(
        "IDs dos Canais",
        value="",
        height=150
    )
    lista_referencias = [c.strip() for c in canais_ref_texto.split("\n") if c.strip()]

with aba3:
    st.subheader("Painel de Execução")
    st.markdown("Tudo configurado? Clique no botão abaixo para iniciar a garimpagem automática.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    executar_busca = st.button("🔥 INICIAR GARIMPAGEM AGORA")

# Função de busca
def pegar_dados_canal(youtube_client, canal_id, origem="Busca automática"):
    try:
        stats = youtube_client.channels().list(
            id=canal_id, part="statistics,snippet"
        ).execute()["items"][0]
        
        nome = stats["snippet"]["title"]
        data_criacao = stats["snippet"]["publishedAt"]
        foto_url = stats["snippet"]["thumbnails"]["high"]["url"]
        pais = stats["snippet"].get("country", "Não informado")
        
        inscritos = int(stats["statistics"].get("subscriberCount", 0))
        total_visualizacoes = int(stats["statistics"].get("viewCount", 0))
        qtd_videos = int(stats["statistics"].get("videoCount", 0))
        
        media_por_video = total_visualizacoes / qtd_videos if qtd_videos > 0 else 0
        relacao = media_por_video / inscritos if inscritos > 0 else 0
        
        return {
            "foto": foto_url,
            "nome": nome,
            "canal_id": canal_id,
            "inscritos": inscritos,
            "media_visualizacoes_video": round(media_por_video),
            "relacao_vid_ins": round(relacao, 2),
            "data_criacao": data_criacao[:10],
            "pais": pais,
            "url": f"https://youtube.com/channel/{canal_id}",
            "origem": origem
        }
    except Exception as e:
        return None

if executar_busca:
    if not chave_api:
        st.error("⚠️ Por favor, insira a Chave da API.")
    else:
        try:
            youtube = build("youtube", "v3", developerKey=chave_api)
            todos_canais = []
            
            with st.spinner(f"🔍 A garimpar canais de '{nicho}'... Por favor aguarde."):
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
                st.success(f"🎉 Garimpagem concluída! {len(todos_canais)} canais encontrados.")
                df = pd.DataFrame(todos_canais)
                
                # Exibir tabela interativa
                st.dataframe(df, use_container_width=True)
                
                # Botão de download do Excel
                nome_arquivo = f"canais-{nicho.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(nome_arquivo, index=False)
                
                with open(nome_arquivo, "rb") as file:
                    st.download_button(
                        label="📥 Descarregar Planilha Excel",
                        data=file,
                        file_name=nome_arquivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("⚠️ Nenhum canal encontrado com estes filtros rigorosos. Tente ajustar os limites na aba de configurações.")
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro ao executar a busca: {e}")
