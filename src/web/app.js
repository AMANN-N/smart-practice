const app = {
    state: {
        topic: null,
        currentQ: null,
        user: "user_web"
    },

    init: async function () {
        console.log("🚀 App v11 Initialized");

        // Wait briefly for Graph
        setTimeout(() => {
            if (window.Graph) {
                try { Graph.init(); } catch (e) { console.error(e); }
            }
        }, 100);

        await this.loadTopics();
    },

    loadTopics: async function () {
        const container = document.getElementById('topic-list');
        if (!container) return;

        try {
            const res = await fetch('/api/topics');
            const data = await res.json();
            const topics = data.topics || [];

            if (topics.length === 0) {
                container.innerHTML = `<p style="text-align: center; color: #888;">No topics found.</p>`;
                return;
            }

            const options = topics.map(t => `<option value="${t}">${t}</option>`).join('');

            container.innerHTML = `
                <div class="topic-selector-group">
                    <select id="topic-dropdown" class="glass-input">
                        ${options}
                    </select>
                    <button id="btn-start" class="btn-glow">
                        <i class="fa-solid fa-play"></i> Start
                    </button>
                </div>
            `;

            // EXPLICIT HANDLER
            document.getElementById('btn-start').onclick = () => this.startSelectedTopic();

        } catch (e) {
            console.error("Load topics failed", e);
            container.innerHTML = `<p style="color: #ff4757;">Connection Error</p>`;
        }
    },

    startSelectedTopic: function () {
        const select = document.getElementById('topic-dropdown');
        if (select && select.value) {
            this.startSession(select.value);
        }
    },

    ingestTopic: async function () {
        const input = document.getElementById('new-topic-input');
        const name = input.value;
        if (!name) return;

        const btn = document.querySelector('.input-group button');
        const origText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic_name: name })
            });
            app.startSession(name);
        } catch (e) {
            alert("Ingestion failed: " + e);
        }
        btn.innerHTML = origText;
    },

    startSession: async function (topicName) {
        this.state.topic = topicName;

        try {
            await fetch('/api/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.state.user, topic_name: topicName })
            });

            document.getElementById('setup-panel').classList.add('hidden');
            document.getElementById('question-panel').classList.remove('hidden');

            if (window.Graph) await Graph.loadData();
            await this.nextQuestion();
        } catch (e) {
            console.error("Session Start Error:", e);
            alert("Could not start session.");
        }
    },

    nextQuestion: async function () {
        document.getElementById('feedback-overlay').classList.add('hidden');
        document.getElementById('options-grid').innerHTML = '';
        document.getElementById('question-content').innerHTML = '<div style="text-align:center; padding: 20px;"><i class="fa-solid fa-spinner fa-spin"></i> Generating...</div>';

        try {
            const res = await fetch('/api/session/next');
            const q = await res.json();
            this.state.currentQ = q;

            if (q.id === "DONE") {
                this.renderDone();
                return;
            }

            this.renderQuestion(q);
            this.updateStats();
        } catch (e) {
            console.error("Next Q Error:", e);
        }
    },

    renderQuestion: function (q) {
        document.getElementById('difficulty-badge').innerText = q.difficulty || "PRACTICE";
        document.getElementById('question-content').innerHTML = q.content;
        if (window.Prism) Prism.highlightAll();

        const grid = document.getElementById('options-grid');

        // Render buttons first to DOM
        grid.innerHTML = q.options.map((opt, idx) =>
            `<button id="opt-${idx}" class="option-btn">${opt}</button>`
        ).join('');

        // ATTACH HANDLERS EXPLICITLY
        q.options.forEach((opt, idx) => {
            const btn = document.getElementById(`opt-${idx}`);
            if (btn) {
                btn.onclick = () => this.submit(opt);
                // Also touchstart for mobile
                btn.ontouchstart = () => this.submit(opt);
            }
        });
    },

    submit: async function (ans) {
        // Prevent double fire if clicked multiple times rapidly
        if (this.submitting) return;
        this.submitting = true;

        const buttons = document.querySelectorAll('.option-btn');
        buttons.forEach(b => b.disabled = true);

        try {
            const res = await fetch('/api/session/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: this.state.currentQ.id,
                    user_answer: ans
                })
            });

            const result = await res.json();

            const overlay = document.getElementById('feedback-overlay');
            overlay.classList.remove('hidden');
            overlay.classList.remove('success', 'error');
            overlay.classList.add(result.is_correct ? 'success' : 'error');

            document.getElementById('feedback-title').innerText = result.is_correct ? "Correct! 🎉" : "Incorrect";
            document.getElementById('feedback-text').innerText = result.feedback;

            // Explicit loop for continues button
            const nextBtn = overlay.querySelector('button');
            if (nextBtn) nextBtn.onclick = () => this.nextQuestion();

            if (result.is_correct && window.Graph) {
                Graph.loadData();
            }
        } catch (e) {
            console.error("Submit Error", e);
            buttons.forEach(b => b.disabled = false);
        } finally {
            this.submitting = false;
        }
    },

    updateStats: async function () {
        try {
            const res = await fetch('/api/session/status');
            const status = await res.json();
            if (status.breadcrumb) {
                document.getElementById('breadcrumb-text').innerText = status.breadcrumb;
            }
            document.getElementById('streak-display').innerText = `🔥 ${status.streak} Streak`;
        } catch (e) { }
    },

    renderDone: function () {
        document.getElementById('question-content').innerHTML = "<h1>🎉 Topic Mastered!</h1>";
        document.getElementById('options-grid').innerHTML = `<button onclick="location.reload()" class="btn-glow">Restart</button>`;
    }
};

window.app = app;
window.addEventListener('load', () => app.init());
