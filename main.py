import os
import time
from urllib.parse import quote
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

HEADLESS = True

VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 5000

DEVICE_SCALE_FACTOR = 2

MAX_SCROLLS = 40

SCROLL_STEP = 900

WAIT_AFTER_SCROLL = 1.0

MAX_RETRIES = 3

USE_STORAGE_STATE = os.path.exists("storage_state.json")


# ==========================================================
# TERMOS
# ==========================================================

TERMOS = [
    "Amstel",
    "Heineken",
    "Cerveja",
    "Cervejas",
    "Cerveja Premium",
    "Pack cerveja",
    "Cerveja zero",
    "Cerveja sem alcool",
    "Brahma",
    "Brahma zero",
    "Budweiser",
    "Budweiser zero",
    "Corona",
    "Corona Cero",
    "Michelob",
    "Spaten",
    "Spaten Pro",
    "Stella",
    "Stella Pure Gold"
]


# ==========================================================
# PASTAS
# ==========================================================

PASTAS = [
    "prints/amazon"
]

for pasta in PASTAS:
    os.makedirs(pasta, exist_ok=True)


# ==========================================================
# AUXILIARES
# ==========================================================

def limpar_nome(nome):
    return (
        nome
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )


def esperar_renderizacao(page):
    try:
        page.wait_for_load_state("domcontentloaded", timeout=30000)
    except:
        pass

    try:
        page.wait_for_load_state("load", timeout=30000)
    except:
        pass

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        pass

    time.sleep(2)


def executar_retry(func):
    erro = None
    for tentativa in range(MAX_RETRIES):
        try:
            return func()
        except PlaywrightTimeoutError as e:
            erro = e
            print(f"⚠ Timeout ({tentativa+1}/{MAX_RETRIES})")
            time.sleep(4)
        except Exception as e:
            erro = e
            print(f"⚠ Erro ({tentativa+1}/{MAX_RETRIES}) -> {e}")
            time.sleep(4)
    raise erro


# ==========================================================
# CONTEXTO
# ==========================================================

def criar_contexto(browser):
    if USE_STORAGE_STATE:
        print("✅ Utilizando storage_state.json")
        return browser.new_context(
            storage_state="storage_state.json",
            viewport={
                "width": VIEWPORT_WIDTH,
                "height": VIEWPORT_HEIGHT
            },
            device_scale_factor=DEVICE_SCALE_FACTOR,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            user_agent=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            )
        )

    print("ℹ storage_state.json não encontrado.")
    return browser.new_context(
        viewport={
            "width": VIEWPORT_WIDTH,
            "height": VIEWPORT_HEIGHT
        },
        device_scale_factor=DEVICE_SCALE_FACTOR,
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        user_agent=(
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0 Safari/537.36"
        )
    )


# ==========================================================
# SCROLL INTELIGENTE (MELHORADO)
# ==========================================================

def scroll_ate_final(page):
    print("⬇ Carregando todos os produtos...")
    altura_anterior = 0
    repeticoes = 0

    while True:
        altura = page.evaluate("""
            () => Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            )
        """)

        posicao = 0
        while posicao < altura:
            page.evaluate(f"window.scrollTo(0, {posicao});")
            time.sleep(0.4)

            try:
                page.wait_for_load_state("networkidle", timeout=1500)
            except:
                pass

            posicao += SCROLL_STEP

        nova_altura = page.evaluate("""
            () => Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            )
        """)

        if nova_altura == altura_anterior:
            repeticoes += 1
        else:
            repeticoes = 0

        altura_anterior = nova_altura
        print(f"   Altura atual: {nova_altura}")

        if repeticoes >= 3:
            break

    print("✅ Scroll concluído.")


# ==========================================================
# VOLTAR AO TOPO
# ==========================================================

def voltar_topo(page):
    page.evaluate("""
        window.scrollTo({
            top:0,
            behavior:'instant'
        });
    """)
    time.sleep(1)


# ==========================================================
# CAPTURA COMPLETA
# ==========================================================

def capturar_pagina(page, arquivo):
    esperar_renderizacao(page)
    time.sleep(3)

    # garante carregamento lazy loading
    scroll_ate_final(page)

    # volta ao topo
    voltar_topo(page)
    esperar_renderizacao(page)
    time.sleep(3)

    print("📸 Capturando screenshot...")
    page.screenshot(
        path=arquivo,
        full_page=True,
        type="png",
        animations="disabled"
    )
    print(f"✅ {arquivo}")


# ==========================================================
# ABERTURA DE URL
# ==========================================================

def abrir_site(page, url):
    def executar():
        page.goto(
            url,
            timeout=180000,
            wait_until="domcontentloaded"
        )
        esperar_renderizacao(page)
        time.sleep(3)
    executar_retry(executar)


# ==========================================================
# PESQUISA + CAPTURA
# ==========================================================

def pesquisar(page, site, termo, url, pasta):
    print()
    print("=" * 70)
    print(site.upper())
    print(termo)
    print("=" * 70)

    nome = limpar_nome(termo)
    arquivo = os.path.join(pasta, f"{nome}.png")

    abrir_site(page, url)
    capturar_pagina(page, arquivo)


# ==========================================================
# EXECUÇÃO
# ==========================================================

def capturar_telas():
    print("🚀 Iniciando automação...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=100,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--start-maximized"
            ]
        )

        context = criar_contexto(browser)
        page = context.new_page()

        SITES = [
            (
                "Amazon",
                "https://www.amazon.com.br/s?k={}",
                "prints/amazon"
            )
        ]

        for site, modelo_url, pasta in SITES:
            print("\n")
            print("=" * 80)
            print(f"INICIANDO {site.upper()}")
            print("=" * 80)

            for termo in TERMOS:
                url = modelo_url.format(quote(termo))
                try:
                    pesquisar(
                        page,
                        site,
                        termo,
                        url,
                        pasta
                    )
                except Exception as erro:
                    print(f"❌ Erro em {site} ({termo})")
                    print(erro)
                    continue

        context.close()
        browser.close()

    print("\n")
    print("🎉 FINALIZADO COM SUCESSO")


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    inicio = time.time()
    capturar_telas()
    fim = time.time()

    print()
    print("=" * 60)
    print(f"Tempo total: {(fim-inicio)/60:.1f} minutos")
    print("=" * 60)
