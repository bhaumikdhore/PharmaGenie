/**
 * PharmaGenie Voice Agent — Frontend
 * Web Speech API (STT) → Backend (Intent + Action) → Speech Synthesis (TTS)
 */

const API_BASE = 'http://localhost:8000';

const conversation = document.getElementById('conversation');
const statusEl = document.getElementById('status');
const micBtn = document.getElementById('micBtn');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');

let recognition = null;
let isListening = false;

function setStatus(text, className = '') {
  statusEl.textContent = text;
  statusEl.className = 'status ' + className;
}

function addMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const avatar = role === 'user' ? '🎤' : '🤖';
  div.innerHTML = `<span class="avatar">${avatar}</span><div class="bubble">${content}</div>`;
  conversation.appendChild(div);
  conversation.scrollTop = conversation.scrollHeight;
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.95;
  u.pitch = 1;
  const voices = speechSynthesis.getVoices();
  const en = voices.find(v => v.lang.startsWith('en')) || voices[0];
  if (en) u.voice = en;
  speechSynthesis.speak(u);
}

async function processText(text) {
  if (!text || !text.trim()) return;
  const trimmed = text.trim();
  addMessage('user', trimmed);
  textInput.value = '';

  setStatus('Processing...', 'processing');
  try {
    const res = await fetch(`${API_BASE}/voice/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: trimmed }),
    });
    const data = await res.json();
    const msg = data.message || 'Done.';
    addMessage('assistant', msg);
    speak(msg);
    setStatus('Ready');
  } catch (e) {
    addMessage('assistant', `Error: ${e.message}. Make sure the backend is running on ${API_BASE}`);
    speak('Sorry, the backend is not available. Please start the server.');
    setStatus('Ready');
  }
}

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    statusEl.textContent = 'Speech recognition not supported in this browser.';
    micBtn.disabled = true;
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-IN'; // English (India) for multilingual support

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add('listening');
    setStatus('Listening...', 'listening');
  };

  recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove('listening');
    if (statusEl.textContent === 'Listening...') setStatus('Ready');
  };

  recognition.onresult = (e) => {
    const transcript = (e.results[0] && e.results[0][0]) ? e.results[0][0].transcript : '';
    if (transcript) processText(transcript);
  };

  recognition.onerror = (e) => {
    isListening = false;
    micBtn.classList.remove('listening');
    setStatus('Ready');
  };
}

function toggleListening() {
  if (!recognition) return;
  if (isListening) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

// Event listeners
micBtn.addEventListener('mousedown', () => recognition && recognition.start());
micBtn.addEventListener('mouseup', () => recognition && recognition.stop());
micBtn.addEventListener('mouseleave', () => recognition && isListening && recognition.stop());
micBtn.addEventListener('touchstart', (e) => { e.preventDefault(); recognition && recognition.start(); });
micBtn.addEventListener('touchend', (e) => { e.preventDefault(); recognition && recognition.stop(); });

sendBtn.addEventListener('click', () => processText(textInput.value));
textInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') processText(textInput.value); });

// Initialize
initSpeechRecognition();
speechSynthesis.getVoices(); // Preload voices
