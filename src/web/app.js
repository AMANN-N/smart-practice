const app = {
    state: {
        topic: null,
        currentQ: null,
        user: "user_web"
    },

    init: async function () {
        Graph.init();
        await this.loadTopics();

        // Check if session active? For now just reset
        // In real app, check /api/session/status
    },

    loadTopics: async function () {
        // We typically would have an endpoint for this. 
        // For MVP, we'll brute force or use Ingestion list
        // Let's mock or fetch from a new endpoint if we had one.
        // I'll add a simple hardcoded list + fetch attempt if we add that EP later.

        // Mocking for now as we didn't explicitly add GET /topics
        const topics = ["python_basics"];
        const container = document.getElementById('topic-list');
        container.innerHTML = topics.map(t =>
            `<button onclick="app.startSession('${t}')" class="option-btn" style="text-align:center">
                <i class="fa-solid fa-book"></i> ${t}
            </button>`
        ).join('');
    },

    ingestTopic: async function () {
        const name = document.getElementById('new-topic-input').value;
        if (!name) return;

        // Show loading state...
        const btn = document.querySelector('.input-group button');
        const origText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic_name: name })
            });
            // Refresh list (mock)
            app.startSession(name);
        } catch (e) {
            alert("Ingestion failed: " + e);
        }
        btn.innerHTML = origText;
    },

    startSession: async function (topicName) {
        this.state.topic = topicName;

        // Start Session API
        await fetch('/api/session/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: this.state.user, topic_name: topicName })
        });

        // Transition UI
        document.getElementById('setup-panel').classList.add('hidden');
        document.getElementById('question-panel').classList.remove('hidden');

        // Load Data
        await Graph.loadData();
        await this.nextQuestion();
    },

    nextQuestion: async function () {
        // Reset UI
        document.getElementById('feedback-overlay').classList.add('hidden');
        document.getElementById('options-grid').innerHTML = '';
        document.getElementById('question-content').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading...';

        // Fetch
        const res = await fetch('/api/session/next');
        const q = await res.json();
        this.state.currentQ = q;

        if (q.id === "DONE") {
            this.renderDone();
            return;
        }

        // Render
        this.renderQuestion(q);
        this.updateStats();
    },

    renderQuestion: function (q) {
        // Breadcrumb logic
        document.getElementById('difficulty-badge').innerText = q.difficulty;

        // Content
        document.getElementById('question-content').innerHTML = q.content;
        // Trigger Prism highlight?
        if (window.Prism) Prism.highlightAll();

        // Options
        const grid = document.getElementById('options-grid');
        grid.innerHTML = q.options.map(opt =>
            `<button onclick="app.submit('${opt}')" class="option-btn">${opt}</button>`
        ).join('');
    },

    submit: async function (ans) {
        // Disable buttons
        document.querySelectorAll('.option-btn').forEach(b => b.disabled = true);

        // API
        const res = await fetch('/api/session/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: this.state.currentQ.id,
                user_answer: ans
            })
        });
        const result = await res.json();

        // Show Feedback
        const overlay = document.getElementById('feedback-overlay');
        const title = document.getElementById('feedback-title');

        overlay.classList.remove('hidden');
        overlay.classList.remove('success', 'error');
        overlay.classList.add(result.is_correct ? 'success' : 'error');

        title.innerText = result.is_correct ? "Correct! 🎉" : "Incorrect";
        document.getElementById('feedback-text').innerText = result.feedback;

        // Refresh Graph to show progress (mastery)
        if (result.is_correct) {
            Graph.loadData();
        }
    },

    updateStats: async function () {
        const res = await fetch('/api/session/status');
        const status = await res.json();

        if (status.breadcrumb) {
            document.getElementById('breadcrumb-text').innerText = status.breadcrumb;
        }
        document.getElementById('streak-display').innerText = `🔥 ${status.streak} Streak`;
    },

    renderDone: function () {
        document.getElementById('question-content').innerHTML = "<h1>🎉 Topic Mastered!</h1><p>You have conquered this knowledge graph.</p>";
        document.getElementById('options-grid').innerHTML = `<button onclick="location.reload()" class="btn-glow">Restart</button>`;
    }
};

// Auto Init
window.addEventListener('load', () => app.init());
