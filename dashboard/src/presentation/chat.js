// Componente de Apresentação do Chatbot Web (Clean Architecture)
export function initChatWidget() {
  if (document.getElementById('chat-widget-container')) return;

  const container = document.createElement('div');
  container.id = 'chat-widget-container';
  container.innerHTML = `
    <button id="chat-toggle-btn" class="chat-toggle-btn" aria-label="Abrir assistente IA">
      <span class="chat-icon">💬</span>
      <span class="chat-label">Perguntar à IA</span>
    </button>
    <div id="chat-window" class="chat-window hidden" role="dialog" aria-labelledby="chat-title">
      <div class="chat-header">
        <div class="chat-title-group">
          <span class="chat-avatar">🤖</span>
          <div>
            <h3 id="chat-title">Assistente IA · WordGen</h3>
            <span class="chat-subtitle"><span class="status-dot"></span> Llama 3.2 3B (Local / GPU)</span>
          </div>
        </div>
        <button id="chat-close-btn" class="chat-close-btn" aria-label="Fechar chat">✕</button>
      </div>
      <div id="chat-messages" class="chat-messages">
        <div class="chat-msg bot">
          <p>Olá! Sou o assistente de IA integrado aos microdados e indicadores do <b>IA - Dataset</b>.</p>
          <p>Posso responder perguntas livres sobre médias de desempenho, idades, modalidades (EJA e Regular), comparações pré/pós, efeito (dz), zonas e escolas.</p>
        </div>
      </div>
      <form id="chat-form" class="chat-form">
        <input id="chat-input" type="text" placeholder="Pergunte sobre os dados, médias, idades ou regras..." autocomplete="off" required />
        <button type="submit" id="chat-send-btn" aria-label="Enviar pergunta">➤</button>
      </form>
    </div>
  `;
  document.body.appendChild(container);

  const toggleBtn = document.getElementById('chat-toggle-btn');
  const chatWindow = document.getElementById('chat-window');
  const closeBtn = document.getElementById('chat-close-btn');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');

  const history = [];

  function formatText(text) {
    let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    html = html.replace(/^\s*#{1,6}\s*(.+?)\s*#*$/gm, '<b>$1</b>');
    html = html.replace(/#{1,6}\s*/g, '');
    html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    html = html.replace(/\*(.*?)\*/g, '<i>$1</i>');
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n- (.*?)(?=\n|$)/g, '<li>$1</li>');
    html = html.replace(/\n/g, '<br/>');
    return `<p>${html}</p>`;
  }

  function appendMsg(sender, text) {
    const div = document.createElement('div');
    div.className = `chat-msg ${sender}`;
    div.innerHTML = formatText(text);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendQuestion(q) {
    if (!q) return;
    appendMsg('user', q);
    input.value = '';
    input.disabled = true;

    // Loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-msg bot loading';
    loadingDiv.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
    messages.appendChild(loadingDiv);
    messages.scrollTop = messages.scrollHeight;

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: q, history})
      });
      const data = await resp.json();
      loadingDiv.remove();
      const reply = data.response || data.error || 'Não foi possível obter resposta.';
      appendMsg('bot', reply);
      history.push({role: 'user', content: q});
      history.push({role: 'assistant', content: reply});
      if (history.length > 8) history.splice(0, 2);
    } catch (e) {
      loadingDiv.remove();
      appendMsg('bot', `Erro de conexão: ${e.message}`);
    } finally {
      input.disabled = false;
      input.focus();
    }
  }

  toggleBtn.addEventListener('click', () => {
    chatWindow.classList.toggle('hidden');
    if (!chatWindow.classList.contains('hidden')) input.focus();
  });

  closeBtn.addEventListener('click', () => {
    chatWindow.classList.add('hidden');
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = input.value.trim();
    sendQuestion(q);
  });
}
