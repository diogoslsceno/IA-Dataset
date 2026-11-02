#!/usr/bin/env python3
"""Servidor HTTP Integrado para o Dashboard e Chatbot de IA (Llama 3.2).

Combina serviço de arquivos estáticos na porta 8765 com endpoints de API para o chatbot:
- POST /api/chat: processa perguntas usando o motor RAG LlamaChatEngine
- GET /api/benchmark: retorna os resultados dos testes de controle
"""
from __future__ import annotations

import http.server
import json
import socketserver
import sys
from pathlib import Path

# Adiciona pasta de Scripts ao PATH
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Scripts"))

from ia_engine import LlamaChatEngine

PORT = 8765
DASHBOARD_DIR = Path(__file__).resolve().parent

# Instância única em memória do motor analítico e de chat
CHAT_ENGINE = LlamaChatEngine()


class DashboardChatHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.send_response(302)
            self.send_header("Location", "/dist/")
            self.end_headers()
            return

        if self.path == "/api/status":
            ollama_ok = CHAT_ENGINE.is_ollama_ready()
            status_data = json.dumps({
                "status": "online",
                "dashboard": "ativo",
                "ollama_ready": ollama_ok,
                "model": "llama3.2:3b" if ollama_ok else "modo_analitico_local",
                "modo": "Neural (Llama 3.2 3B)" if ollama_ok else "Analítico Local (Estatístico)"
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(status_data)))
            self.end_headers()
            self.wfile.write(status_data)
            return

        if self.path == "/api/benchmark":
            bench_file = DASHBOARD_DIR / "data" / "benchmark_ia_resultados.json"
            if bench_file.exists():
                data = bench_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404, "Relatório de benchmark ainda não gerado.")
            return

        # Para as demais rotas estáticas
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                payload = json.loads(body)
                message = payload.get("message", "").strip()
                history = payload.get("history", [])

                if not message:
                    response_text = "Por favor, envie uma pergunta sobre os dados educacionais."
                else:
                    response_text = CHAT_ENGINE.ask(message, history)

                resp_data = json.dumps({"response": response_text}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)
            except Exception as e:
                err_data = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_data)))
                self.end_headers()
                self.wfile.write(err_data)
            return

        self.send_error(404, "Endpoint não encontrado")


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), DashboardChatHandler) as httpd:
        print(f"Servidor Integrado rodando em http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")


if __name__ == "__main__":
    main()
