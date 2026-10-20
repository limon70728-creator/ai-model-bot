<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Модель</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; user-select: none; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0d0d0d;
            color: #fff;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            padding: 30px 20px 40px;
            overflow: hidden;
        }
        .top { text-align: center; width: 100%; }
        .balance { font-size: 42px; font-weight: 700; }
        .balance span { font-size: 18px; color: #888; font-weight: 500; }
        .subtitle { color: #666; font-size: 14px; margin-top: 4px; }
        .tap-area { flex: 1; display: flex; align-items: center; justify-content: center; width: 100%; }
        .coin {
            width: 220px; height: 220px;
            background: radial-gradient(circle at 35% 35%, #ffd700, #ffaa00 40%, #ff8c00);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 80px;
            box-shadow: 0 0 60px rgba(255, 170, 0, 0.4), inset 0 0 30px rgba(255,255,255,0.3);
            cursor: pointer;
            transition: transform 0.1s;
        }
        .coin:active { transform: scale(0.92); }
        .floating {
            position: absolute; font-size: 24px; font-weight: 700; color: #ffd700;
            pointer-events: none; animation: floatUp 0.8s ease-out forwards;
        }
        @keyframes floatUp {
            0% { opacity: 1; transform: translateY(0); }
            100% { opacity: 0; transform: translateY(-80px); }
        }
        .bottom { width: 100%; display: flex; gap: 12px; }
        .bottom button {
            flex: 1; background: #1a1a1a; border: 1px solid #333; color: #fff;
            border-radius: 14px; padding: 14px; font-size: 15px;
        }
    </style>
</head>
<body>
    <div class="top">
        <div class="balance"><span id="balance">...</span> <span>монеток</span></div>
        <div class="subtitle">тапай и зарабатывай</div>
    </div>

    <div class="tap-area">
        <div class="coin" id="coin">⭐</div>
    </div>

    <div class="bottom">
        <button onclick="Telegram.WebApp.showAlert('Скоро')">Задания</button>
        <button onclick="Telegram.WebApp.showAlert('Скоро')">Магазин</button>
        <button onclick="Telegram.WebApp.showAlert('Скоро')">Купить</button>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        const API = "https://ai-model-bot-production.up.railway.app";
        const user = tg.initDataUnsafe.user;
        const userId = user ? user.id : null;
        const balanceEl = document.getElementById("balance");
        const coin = document.getElementById("coin");

        async function loadBalance() {
            if (!userId) return;
            try {
                const res = await fetch(`${API}/balance/${userId}`);
                const data = await res.json();
                balanceEl.textContent = data.balance;
            } catch (e) {
                balanceEl.textContent = "0";
            }
        }

        async function tap() {
            if (!userId) return;
            try {
                const res = await fetch(`${API}/tap`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: userId })
                });
                const data = await res.json();
                balanceEl.textContent = data.balance;

                const plus = document.createElement("div");
                plus.className = "floating";
                plus.textContent = "+1";
                plus.style.left = (coin.offsetLeft + 90) + "px";
                plus.style.top = (coin.offsetTop + 40) + "px";
                document.body.appendChild(plus);
                setTimeout(() => plus.remove(), 800);

                if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
            } catch (e) {
                console.error(e);
            }
        }

        coin.onclick = tap;
        loadBalance();
    </script>
</body>
</html>
