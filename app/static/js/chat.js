// app/static/js/chat.js
document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    let chatSessionId = null; // Храним ID сессии чата

    // Функция для добавления сообщения в окно чата
    function addMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = text;
        chatWindow.appendChild(messageElement);
        // Прокручиваем вниз
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Обработчик отправки формы
    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Отменяем стандартную отправку формы
        const userMessage = messageInput.value.trim();
        if (!userMessage) return;

        addMessage(userMessage, 'user');
        messageInput.value = '';
        sendButton.disabled = true;
        sendButton.textContent = 'Думаю...';

        try {
            // Формируем данные для отправки
            // Убираем выбор модели, теперь всегда используем только GigaChat
            const requestData = {
                message_content: userMessage
            };
            
            // Только добавляем session_id если он существует
            if (chatSessionId !== null) {
                requestData.session_id = chatSessionId;
            }

            const response = await fetch('/api/v1/chat/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${JWT_TOKEN}` // Используем токен, полученный из шаблона
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                // Если токен истек или невалиден
                if (response.status === 401) {
                    addMessage('Ваша сессия истекла. Пожалуйста, обновите страницу и войдите снова.', 'assistant');
                    return;
                }
                throw new Error(`Ошибка сервера: ${response.statusText}`);
            }

            const data = await response.json();
            const assistantMessage = data.assistant_message.content;
            chatSessionId = data.session_id; // Сохраняем/обновляем ID сессии

            addMessage(assistantMessage, 'assistant');

        } catch (error) {
            console.error('Ошибка при отправке сообщения:', error);
            addMessage('Произошла ошибка. Пожалуйста, попробуйте еще раз.', 'assistant');
        } finally {
            sendButton.disabled = false;
            sendButton.textContent = 'Отправить';
        }
    });
});