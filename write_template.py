html = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAIA - مساعد التأمين الذكي</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Tajawal', 'Segoe UI', Tahoma, sans-serif;
            background: linear-gradient(135deg, #1a5f7a 0%, #0d3d4d 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
        }
        .chat-container {
            width: 100%;
            max-width: 480px;
            height: 95vh;
            max-height: 800px;
            background: #fff;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #1a5f7a 0%, #0d3d4d 100%);
            color: white;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header-info { display: flex; align-items: center; gap: 12px; }
        .logo {
            width: 45px; height: 45px;
            background: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        .header-text h1 { font-size: 18px; font-weight: 700; margin-bottom: 2px; }
        .header-text p { font-size: 11px; opacity: 0.85; }
        .header-actions { display: flex; align-items: center; gap: 8px; }
        .stage-badge {
            background: rgba(255,255,255,0.15);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
        }
        .header-btn {
            background: rgba(255,255,255,0.15);
            border: none;
            color: white;
            width: 36px; height: 36px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
        }
        .header-btn:hover { background: rgba(255,255,255,0.25); }
        .progress-container {
            background: #f0f4f8;
            padding: 12px 16px;
            border-bottom: 1px solid #e0e5eb;
        }
        .progress-bar {
            height: 6px;
            background: #e0e5eb;
            border-radius: 3px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            border-radius: 3px;
            transition: width 0.5s ease;
            width: 10%;
        }
        .progress-text {
            display: flex;
            justify-content: space-between;
            margin-top: 6px;
            font-size: 10px;
            color: #666;
        }
        .chat-messages {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            background: #f8fafc;
        }
        .message {
            margin-bottom: 14px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user { justify-content: flex-end; }
        .message.assistant { justify-content: flex-start; }
        .message-content {
            max-width: 85%;
            padding: 14px 18px;
            border-radius: 20px;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #1a5f7a 0%, #0d3d4d 100%);
            color: white;
            border-bottom-right-radius: 6px;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 6px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .typing-indicator {
            padding: 14px 18px;
            background: white;
            border-radius: 20px;
            width: fit-content;
            display: flex;
            gap: 4px;
        }
        .typing-indicator span {
            width: 8px; height: 8px;
            background: #1a5f7a;
            border-radius: 50%;
            animation: bounce 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-8px); }
        }
        .quick-actions {
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #e8ecf0;
            display: flex;
            gap: 8px;
            overflow-x: auto;
        }
        .quick-action {
            padding: 10px 16px;
            background: #f0f4f8;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            font-family: inherit;
            white-space: nowrap;
            color: #333;
        }
        .quick-action:hover {
            background: #1a5f7a;
            color: white;
        }
        .chat-input {
            padding: 16px;
            background: white;
            border-top: 1px solid #e8ecf0;
            display: flex;
            gap: 12px;
        }
        .chat-input input {
            flex: 1;
            padding: 14px 20px;
            border: 2px solid #e8ecf0;
            border-radius: 25px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
        }
        .chat-input input:focus { border-color: #1a5f7a; }
        .send-btn {
            width: 50px; height: 50px;
            background: linear-gradient(135deg, #1a5f7a 0%, #0d3d4d 100%);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
        }
        .send-btn:disabled { opacity: 0.5; }
        .chat-footer {
            padding: 10px;
            background: #f8fafc;
            text-align: center;
            font-size: 10px;
            color: #999;
        }
        @media (max-width: 500px) {
            body { padding: 0; }
            .chat-container { height: 100vh; max-height: none; border-radius: 0; }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="header-info">
                <div class="logo">🚗</div>
                <div class="header-text">
                    <h1>SAIA Insurance</h1>
                    <p>مساعدك الذكي لتأمين السيارات</p>
                </div>
            </div>
            <div class="header-actions">
                <div class="stage-badge" id="stageBadge">📍 البداية</div>
                <button class="header-btn" onclick="resetChat()" title="محادثة جديدة">🔄</button>
            </div>
        </div>
        <div class="progress-container">
            <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
            <div class="progress-text">
                <span id="progressStage">الترحيب</span>
                <span id="progressPercent">10%</span>
            </div>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                <div class="message-content">مرحباً بك في SAIA! 👋

أنا مساعدك الذكي لتأمين السيارات في السعودية.

🛡️ نقدم لك:
• تأمين شامل
• تأمين ضد الغير
• تأمين شامل بلس

كيف يمكنني مساعدتك اليوم؟</div>
            </div>
        </div>
        <div class="quick-actions" id="quickActions">
            <button class="quick-action" onclick="send('تأمين شامل')">🛡️ تأمين شامل</button>
            <button class="quick-action" onclick="send('تأمين ضد الغير')">📋 ضد الغير</button>
            <button class="quick-action" onclick="send('تأمين شامل بلس')">⭐ شامل بلس</button>
        </div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="اكتب رسالتك هنا..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
        </div>
        <div class="chat-footer">SAIA Insurance © 2026 | مرخصة من البنك المركزي السعودي</div>
    </div>
    <script>
        const API_URL = '/api/ai/chat/';
        let conversationId = null;
        const phone = '96655' + Math.floor(1000000 + Math.random() * 9000000);
        
        const stageConfig = {
            'greeting': { name: 'البداية', progress: 10, btns: ['🛡️ تأمين شامل|تأمين شامل', '📋 ضد الغير|تأمين ضد الغير', '⭐ شامل بلس|تأمين شامل بلس'] },
            'service_details': { name: 'نوع التأمين', progress: 20, btns: ['🛡️ شامل|تأمين شامل', '📋 ضد الغير|تأمين ضد الغير'] },
            'collecting_vehicle': { name: 'بيانات السيارة', progress: 30, btns: ['📝 مثال|تويوتا كامري 2024 قيمتها 120000 لوحة أ ب ج 1234'] },
            'confirming_vehicle': { name: 'تأكيد السيارة', progress: 45, btns: ['✅ صحيحة|نعم صحيحة', '✏️ تعديل|أريد تعديل البيانات'] },
            'showing_offers': { name: 'العروض', progress: 55, btns: ['1️⃣ العرض 1|العرض 1', '2️⃣ العرض 2|العرض 2', '3️⃣ العرض 3|العرض 3'] },
            'offer_details': { name: 'تفاصيل العرض', progress: 65, btns: ['✅ موافق|موافق', '🔄 عرض آخر|أريد عرض آخر'] },
            'collecting_profile': { name: 'البيانات الشخصية', progress: 75, btns: ['📝 مثال|رقم هويتي 1234567890 وتاريخ ميلادي 1990-05-15'] },
            'confirming_profile': { name: 'تأكيد البيانات', progress: 85, btns: ['✅ صحيحة|نعم صحيحة'] },
            'order_summary': { name: 'ملخص الطلب', progress: 90, btns: ['✅ تأكيد|تأكيد الطلب'] },
            'payment_pending': { name: 'الدفع', progress: 95, btns: ['💳 تم الدفع|تم الدفع'] },
            'completed': { name: 'مكتمل ✓', progress: 100, btns: ['🆕 طلب جديد|أريد طلب جديد'] }
        };

        function addMessage(content, isUser) {
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user' : 'assistant');
            div.innerHTML = '<div class="message-content">' + content.replace(/(https?:\\/\\/[^\\s]+)/g, '<a href="$1" target="_blank">$1</a>') + '</div>';
            document.getElementById('chatMessages').appendChild(div);
            document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
        }

        function showTyping() {
            const div = document.createElement('div');
            div.className = 'message assistant';
            div.id = 'typingIndicator';
            div.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            document.getElementById('chatMessages').appendChild(div);
            document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
        }

        function hideTyping() { const el = document.getElementById('typingIndicator'); if (el) el.remove(); }

        function updateStage(stage) {
            const config = stageConfig[stage] || stageConfig['greeting'];
            document.getElementById('stageBadge').textContent = '📍 ' + config.name;
            document.getElementById('progressFill').style.width = config.progress + '%';
            document.getElementById('progressStage').textContent = config.name;
            document.getElementById('progressPercent').textContent = config.progress + '%';
            document.getElementById('quickActions').innerHTML = config.btns.map(b => {
                const [label, value] = b.split('|');
                return '<button class="quick-action" onclick="send(\\'' + value + '\\')">' + label + '</button>';
            }).join('');
        }

        function setLoading(loading) {
            document.getElementById('sendBtn').disabled = loading;
            document.getElementById('messageInput').disabled = loading;
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            input.value = '';
            send(message);
        }

        async function send(message) {
            addMessage(message, true);
            showTyping();
            setLoading(true);
            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message, conversation_id: conversationId, phone: phone })
                });
                const data = await response.json();
                hideTyping();
                setLoading(false);
                if (data.conversation_id) conversationId = data.conversation_id;
                if (data.stage) updateStage(data.stage);
                if (data.response) addMessage(data.response, false);
            } catch (error) {
                hideTyping();
                setLoading(false);
                addMessage('⚠️ حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.', false);
            }
        }

        function resetChat() {
            if (!confirm('هل تريد بدء محادثة جديدة؟')) return;
            conversationId = null;
            document.getElementById('chatMessages').innerHTML = '<div class="message assistant"><div class="message-content">مرحباً بك في SAIA! 👋\\n\\nأنا مساعدك الذكي لتأمين السيارات.\\n\\n🛡️ نقدم لك:\\n• تأمين شامل\\n• تأمين ضد الغير\\n• تأمين شامل بلس\\n\\nكيف يمكنني مساعدتك اليوم؟</div></div>';
            updateStage('greeting');
        }

        document.getElementById('messageInput').focus();
    </script>
</body>
</html>"""

with open('templates/chat_v2.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done! Written', len(html), 'bytes')
