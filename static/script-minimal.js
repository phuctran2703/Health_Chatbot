// Health Chatbot JavaScript - Optimized for Tailwind CSS
let isLoading = false;
let messageCount = 0;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const toastContainer = document.getElementById('toastContainer');
const charCount = document.querySelector('.char-count');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    updateCharCount();
    focusInput();
    checkApiHealth();
});

// Event listeners
function setupEventListeners() {
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        updateCharCount();
        updateSendButton();
    });
}

// Update character count
function updateCharCount() {
    const length = messageInput.value.length;
    charCount.textContent = `${length}/500`;
    charCount.className = length > 450 ? 'char-count text-red-500 font-bold' : 'char-count font-medium text-gray-400';
}

// Update send button state
function updateSendButton() {
    const hasText = messageInput.value.trim().length > 0;
    const canSend = hasText && !isLoading;
    
    sendButton.disabled = !canSend;
    sendButton.className = canSend 
        ? 'bg-gradient-to-br from-indigo-500 to-purple-600 border-none rounded-full w-9 h-9 text-white cursor-pointer flex items-center justify-center transition-all duration-300 hover:scale-105 hover:shadow-md flex-shrink-0'
        : 'bg-gray-400 border-none rounded-full w-9 h-9 text-white cursor-not-allowed flex items-center justify-center transition-all duration-300 flex-shrink-0';
}

// Main send message function
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    // Add user message
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    updateCharCount();
    updateSendButton();
    
    // Hiển thị tin nhắn "đang phân tích"
    const analysisMessageId = addMessage('Đang phân tích và tìm kiếm thông tin...', 'bot');
    isLoading = true;
    updateSendButton();
    
    try {
        await streamResponse(message, analysisMessageId);
    } catch (error) {
        console.error('Error:', error);
        // Xóa tin nhắn "đang phân tích" và hiển thị lỗi
        removeMessage(analysisMessageId);
        addMessage(getErrorMessage(error), 'bot', null, true, false);
        showToast('Có lỗi xảy ra khi kết nối với server', 'error');
    } finally {
        isLoading = false;
        updateSendButton();
    }
    
    messageCount++;
    focusInput();
}

// Stream response function
async function streamResponse(message, analysisMessageId) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: message })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    // Xóa tin nhắn "đang phân tích"
    removeMessage(analysisMessageId);
    
    let streamMessageId = null;
    let aiPowered = false;
    let currentContent = '';
    
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'metadata') {
                            aiPowered = data.ai_powered;
                            // Tạo message container trống
                            streamMessageId = addMessage('', 'bot', null, false, aiPowered);
                        } else if (data.type === 'chunk' && streamMessageId) {
                            currentContent += data.content;
                            updateStreamMessage(streamMessageId, currentContent, aiPowered);
                        } else if (data.type === 'word' && streamMessageId) {
                            currentContent += (currentContent ? ' ' : '') + data.content;
                            updateStreamMessage(streamMessageId, currentContent, aiPowered);
                        } else if (data.type === 'end') {
                            // Xóa typing cursor khi stream kết thúc
                            if (streamMessageId) {
                                const messageElement = document.getElementById(streamMessageId);
                                if (messageElement) {
                                    const bubbleDiv = messageElement.querySelector('.message-bubble');
                                    if (bubbleDiv) {
                                        bubbleDiv.innerHTML = formatMessage(currentContent);
                                    }
                                }
                            }
                            // Stream hoàn thành
                            break;
                        }
                    } catch (parseError) {
                        console.error('Parse error:', parseError);
                    }
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

// Update streaming message
function updateStreamMessage(messageId, content, aiPowered) {
    const messageElement = document.getElementById(messageId);
    if (!messageElement) return;
    
    const bubbleDiv = messageElement.querySelector('.message-bubble');
    if (bubbleDiv) {
        bubbleDiv.innerHTML = formatMessage(content);
        scrollToBottom();
    }
}

// Add message with Tailwind classes
function addMessage(content, type = 'bot', sources = null, isError = false, aiPowered = false) {
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `flex mb-6 message-enter ${type === 'user' ? 'flex-row-reverse' : ''}`;
    
    // Avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = `flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white ${
        type === 'user' 
            ? 'ml-3 bg-gradient-to-br from-pink-500 to-purple-600' 
            : aiPowered 
                ? 'mr-3 bg-gradient-to-br from-green-500 to-blue-600'
                : 'mr-3 bg-gradient-to-br from-indigo-500 to-purple-600'
    }`;
    avatarDiv.innerHTML = `<i class="fas fa-${type === 'user' ? 'user' : aiPowered ? 'brain' : 'robot'} text-xs"></i>`;
    
    // Content container
    const contentDiv = document.createElement('div');
    contentDiv.className = `max-w-4xl flex flex-col ${type === 'user' ? 'items-end' : ''}`;
    
    // AI Badge
    let aiBadge = '';
    if (aiPowered && type === 'bot') {
        aiBadge = ``;
    }
    
    // Message bubble
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = `message-bubble p-4 rounded-xl shadow-sm mb-2 border text-sm font-normal leading-relaxed ${
        type === 'user' 
            ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-br-lg border-indigo-200' 
            : isError 
                ? 'bg-red-50 border-red-200 rounded-bl-lg text-red-700' 
                : aiPowered
                    ? 'bg-gradient-to-br from-green-50 to-blue-50 border-green-200 rounded-bl-lg text-gray-800'
                    : 'bg-gray-50 border-gray-200 rounded-bl-lg text-gray-800'
    }`;
    
    bubbleDiv.innerHTML = aiBadge + formatMessage(content);
    
    // Add sources (không còn sử dụng vì không truy cập database)
    // if (sources && sources.length > 0 && !isError) {
    //     ... source code removed
    // }
    
    // Timestamp
    const timeDiv = document.createElement('div');
    timeDiv.className = 'text-xs text-gray-400 mt-1';
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    timeDiv.textContent = `${hours}:${minutes}`;
    
    contentDiv.appendChild(bubbleDiv);
    contentDiv.appendChild(timeDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    return messageId;
}

// Remove message by ID
function removeMessage(messageId) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.remove();
    }
}

// Format message content
function formatMessage(content) {
    return content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-2 py-1 rounded text-sm">$1</code>');
}

// Toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="flex items-center gap-2">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toastContainer.contains(toast)) {
                toastContainer.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Error handling
function getErrorMessage(error) {
    if (error.message.includes('Failed to fetch')) {
        return `<strong>Không thể kết nối với server</strong><br>
                Vui lòng kiểm tra kết nối mạng và thử lại sau.<br><br>
                <em>💡 Gợi ý: Đảm bảo server đang chạy và ChromaDB đã được khởi động.</em>`;
    } else if (error.message.includes('500')) {
        return `<strong>Lỗi server nội bộ</strong><br>
                Server đang gặp sự cố kỹ thuật. Vui lòng thử lại sau ít phút.`;
    } else {
        return `<strong>Đã xảy ra lỗi không xác định</strong><br>
                ${error.message}<br><br>
                <em>Vui lòng thử lại hoặc liên hệ quản trị viên nếu lỗi tiếp tục xảy ra.</em>`;
    }
}

// Utility functions
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

function focusInput() {
    setTimeout(() => messageInput.focus(), 100);
}

// API health check
async function checkApiHealth() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            const data = await response.json();
            console.log('API Health:', data);
            if (data.chromadb_status !== 'connected') {
                showToast('ChromaDB chưa kết nối - một số tính năng có thể bị hạn chế', 'warning');
            }
            if (data.gemini_ai_status === 'available') {
                showToast('Gemini AI đã sẵn sàng - chatbot được hỗ trợ AI', 'success');
            } else if (data.gemini_ai_status === 'not_configured') {
                showToast('Chưa cấu hình Gemini AI - chạy ở chế độ cơ bản', 'info');
            }
        }
    } catch (error) {
        console.error('Health check failed:', error);
        showToast('Không thể kiểm tra trạng thái server', 'warning');
    }
}
