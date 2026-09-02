// GuessWhoAmI Game - Frontend Logic
class GuessWhoAmIGame {
  constructor() {
    this.sessionId = null;
    this.remainingQuestions = 20;
    this.remainingHints = 3;

    this.initializeEventListeners();
  }

  // Initialize event listeners
  initializeEventListeners() {
    // Start game button (HTML id="start-game")
    document.getElementById('start-game')
        .addEventListener('click', () => this.startNewGame());

    // Send message button (HTML id="send-btn")
    document.getElementById('send-btn')
        .addEventListener('click', () => this.sendMessage());

    // User input enter key (HTML id="user-input")
    document.getElementById('user-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });

    // Hint button (HTML id="get-hint")
    document.getElementById('get-hint')
        .addEventListener('click', () => this.requestHint());

    // Guess button (HTML id="guess-btn")
    document.getElementById('guess-btn')
        .addEventListener('click', () => this.submitGuess());

    // Play again button (HTML id="play-again")
    document.getElementById('play-again')
        .addEventListener('click', () => this.restartGame());
  }

  // Start new game
  async startNewGame() {
    try {
      this.setStartBtnLoading(true);
      this.showLoadingOverlay();

      const response = await fetch('http://localhost:8000/api/game/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const result = await response.json();

      if (!result.success) throw new Error(result.error || 'Не удалось запустить');

      const data = result.data;
      this.sessionId = data.session_id;
      this.remainingQuestions = data.max_questions || 20;
      this.remainingHints = data.max_hints || 3;

      // Switch to game screen
      document.getElementById('intro-section').classList.add('hidden');
      document.getElementById('game-section').classList.remove('hidden');
      document.getElementById('result-modal').classList.add('hidden');

      // Enable controls
      document.getElementById('user-input').disabled = false;
      document.getElementById('send-btn').disabled = false;
      document.getElementById('get-hint').disabled = false;
      document.getElementById('guess-btn').disabled = false;
      document.getElementById('guess-input').disabled = false;

      // Clear chat and add welcome message
      this.clearChat();
      this.addMessage(data.welcome_message, 'agent');

      // Update stats
      this.updateStats();

    } catch (error) {
      alert(`Не удалось начать игру: ${
          error.message}\nУбедитесь, что бэкенд запущен на http://localhost:8000`);
      console.error('Start game error:', error);
    } finally {
      this.hideLoadingOverlay();
      this.setStartBtnLoading(false);
    }
  }

  // Send message to agent
  async sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();

    if (!message) return;
    if (!this.sessionId) {
      alert('Сначала начните игру');
      return;
    }

    input.value = '';
    this.addMessage(message, 'user');
    this.setControlsDisabled(true);

    try {
      const response = await fetch('http://localhost:8000/api/game/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: this.sessionId, message: message})
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const result = await response.json();

      if (!result.success) throw new Error(result.error || 'Не удалось отправить сообщение');

      const data = result.data;
      this.addMessage(data.response, 'agent');

      // Update remaining questions from server
      this.remainingQuestions = data.remaining_questions;
      this.updateStats();

      if (data.is_game_over) {
        this.endGame(false);
      }

    } catch (error) {
      this.addMessage(`⚠️ Ошибка отправки: ${error.message}`, 'agent');
      console.error('Send message error:', error);
    } finally {
      this.setControlsDisabled(false);
    }
  }

  // Request hint
  async requestHint() {
    if (!this.sessionId) return;
    if (this.remainingHints <= 0) {
      alert('Подсказки закончились');
      return;
    }

    this.setControlsDisabled(true);

    try {
      const response = await fetch('http://localhost:8000/api/game/hint', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: this.sessionId})
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const result = await response.json();

      if (!result.success) throw new Error(result.error || 'Не удалось получить подсказку');

      const data = result.data;
      const hintText = data.hint || data.message || 'Подсказок нет';
      this.addMessage(`💡 Подсказка: ${hintText}`, 'agent');

      this.remainingHints = data.remaining_hints !== undefined ?
          data.remaining_hints :
          this.remainingHints - 1;
      this.updateStats();

    } catch (error) {
      alert(`Не удалось получить подсказку：${error.message}`);
      console.error('Hint error:', error);
    } finally {
      this.setControlsDisabled(false);
    }
  }

  // Submit guess
  async submitGuess() {
    const guessInput = document.getElementById('guess-input');
    const guess = guessInput.value.trim();

    if (!guess) {
      alert('Введите имя для угадывания');
      return;
    }
    if (!this.sessionId) return;

    this.setControlsDisabled(true);

    try {
      const response = await fetch('http://localhost:8000/api/game/guess', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: this.sessionId, guess: guess})
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const result = await response.json();

      if (!result.success) throw new Error(result.error || 'Ошибка угадывания');

      const data = result.data;
      guessInput.value = '';

      if (data.is_correct) {
        this.addMessage(`🎉 Поздравляем! Верно: ${guess}`, 'agent');
        this.endGame(true, data.figure_info, data.portrait_images || []);
      } else {
        this.addMessage(`❌ Неверно! ${data.message || 'Подумайте ещё~'}`, 'agent');
        this.remainingQuestions = data.remaining_questions !== undefined ?
            data.remaining_questions :
            this.remainingQuestions - 1;
        this.updateStats();

        if (data.is_game_over || this.remainingQuestions <= 0) {
          this.endGame(false);
        }
      }

    } catch (error) {
      alert(`Ошибка отправки догадки: ${error.message}`);
      console.error('Guess error:', error);
    } finally {
      this.setControlsDisabled(false);
    }
  }

  // End game and show result
  async endGame(isWin, figureInfo = null, portraitImages = []) {
    // Disable controls
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-btn').disabled = true;
    document.getElementById('get-hint').disabled = true;
    document.getElementById('guess-btn').disabled = true;
    document.getElementById('guess-input').disabled = true;

    // Fetch figure info if not provided
    if (!figureInfo && this.sessionId) {
      try {
        const response = await fetch('http://localhost:8000/api/game/end', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({session_id: this.sessionId})
        });
        if (response.ok) {
          const result = await response.json();
          if (result.success && result.data) {
            figureInfo = result.data;
          }
        }
      } catch (e) {
        console.error('End game fetch error:', e);
      }
    }

    // Show result modal
    document.getElementById('result-modal').classList.remove('hidden');

    const resultTitle = document.getElementById('result-title');
    const resultMessage = document.getElementById('result-message');
    const figureInfoEl = document.getElementById('figure-info');

    if (isWin) {
      resultTitle.textContent = '🎉 Поздравляем, вы угадали!';
      resultMessage.textContent = 'Вы угадали личность!';
    } else {
      resultTitle.textContent = '⏰ Игра окончена';
      resultMessage.textContent = 'Вопросы закончились — в следующий раз повезёт!';
    }

    if (figureInfo) {
      const name = figureInfo.figure_name || figureInfo.name || 'неизвестно';
      const dynasty = figureInfo.dynasty || '';
      const occupation = figureInfo.occupation || figureInfo.profession || '';
      const achievements = figureInfo.achievements || '';
      const characteristics =
          figureInfo.characteristics || figureInfo.key_features || '';

      // Build portrait gallery HTML
      let portraitHtml = '';
      if (portraitImages && portraitImages.length > 0) {
        const imgItems = portraitImages
                             .map(photo => `
          <div class="portrait-item">
            <img src="${photo.url}" alt="${photo.description || name}"
                 title="📷 ${photo.photographer || 'Unsplash'}"
                 onerror="this.parentElement.style.display='none'">
          </div>
        `).join('');
        portraitHtml = `<div class="portrait-gallery">${imgItems}</div>`;
      }

      figureInfoEl.innerHTML = `
        ${portraitHtml}
        <p><strong>Ответ:</strong>${name}</p>
        ${dynasty ? `<p><strong>Эпоха/династия:</strong>${dynasty}</p>` : ''}
        ${occupation ? `<p><strong>Профессия/роль:</strong>${occupation}</p>` : ''}
        ${
          achievements ? `<p><strong>Главные достижения:</strong>${achievements}</p>` :
                         ''}
        ${
          characteristics ?
              `<p><strong>Ключевые черты:</strong>${characteristics}</p>` :
              ''}
      `;
    } else {
      figureInfoEl.innerHTML = '';
    }

    this.sessionId = null;
  }

  // Restart game
  restartGame() {
    document.getElementById('result-modal').classList.add('hidden');
    document.getElementById('game-section').classList.add('hidden');
    document.getElementById('intro-section').classList.remove('hidden');
    this.clearChat();
    this.sessionId = null;
    this.remainingQuestions = 20;
    this.remainingHints = 3;
  }

  // Add message to chat
  addMessage(text, type) {
    const chatContainer = document.getElementById('chat-container');

    // Remove static welcome message on first real message
    const staticWelcome = chatContainer.querySelector('.welcome-message');
    if (staticWelcome) staticWelcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  // Clear chat
  clearChat() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.innerHTML = `
      <div class="welcome-message">
        <div class="message agent-message">
          <div class="message-content">
            Привет! Я известная личность — угадайте, кто я, задавая вопросы. Начнём!
          </div>
        </div>
      </div>`;
  }

  // Update stats display
  updateStats() {
    document.getElementById('remaining-questions').textContent =
        `Осталось вопросов: ${this.remainingQuestions}`;
    document.getElementById('remaining-hints').textContent =
        `Осталось подсказок: ${this.remainingHints}`;
  }

  // Disable/enable game controls
  setControlsDisabled(disabled) {
    document.getElementById('send-btn').disabled = disabled;
    document.getElementById('get-hint').disabled = disabled;
    document.getElementById('guess-btn').disabled = disabled;
    document.getElementById('user-input').disabled = disabled;
    document.getElementById('guess-input').disabled = disabled;
  }

  // Start button loading state
  setStartBtnLoading(loading) {
    const btn = document.getElementById('start-game');
    btn.disabled = loading;
    btn.textContent = loading ? 'Запуск...' : 'Начать игру';
  }

  // Show full-screen loading overlay with step text rotation
  showLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    const stepEl = document.getElementById('loading-step');
    overlay.classList.remove('hidden');

    const steps = [
      '🔍 Случайный выбор личности...',
      '📚 Поиск сведений о личности...',
      '🤖 ИИ готовит подсказки...',
      '🎤 Подготовка ролевой игры...',
    ];
    let idx = 0;
    stepEl.textContent = steps[0];

    this._loadingTimer = setInterval(() => {
      idx = (idx + 1) % steps.length;
      stepEl.style.opacity = '0';
      setTimeout(() => {
        stepEl.textContent = steps[idx];
        stepEl.style.opacity = '1';
      }, 400);
    }, 2000);
  }

  // Hide loading overlay and clear timer
  hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('hidden');
    if (this._loadingTimer) {
      clearInterval(this._loadingTimer);
      this._loadingTimer = null;
    }
  }
}

// Initialize game on page load
window.onload = function() {
  window.game = new GuessWhoAmIGame();
};