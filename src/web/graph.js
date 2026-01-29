const Graph = {
    cy: null,

    init: function () {
        console.log("🕸️ Graph.init called via v6");

        const container = document.getElementById('cy');
        if (!container) {
            console.error("CRITICAL: #cy container not found");
            return;
        }

        // VISUAL CONFIRMATION
        container.style.border = "1px solid #6c5ce7";

        // Init Cytoscape
        this.cy = cytoscape({
            container: container,
            wheelSensitivity: 0.2,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#1e1e2e',
                        'label': 'data(label)',
                        'color': '#dfe6e9',
                        'font-size': '14px',
                        'font-family': 'Outfit, sans-serif',
                        'font-weight': '500',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'width': 'label',
                        'padding': '12px',
                        'shape': 'round-rectangle',
                        'border-width': 1,
                        'border-color': '#636e72',
                        'text-wrap': 'wrap',
                        'text-max-width': '120px'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#636e72',
                        'curve-style': 'taxi',
                        'taxi-direction': 'downward',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#636e72',
                        'arrow-scale': 1.2
                    }
                },
                {
                    selector: 'node[status = "active"]',
                    style: {
                        'background-color': '#646cff',
                        'border-color': '#aeb4ff',
                        'color': '#fff',
                        'border-width': 2,
                        'shadow-blur': 10,
                        'shadow-color': '#646cff'
                    }
                },
                {
                    selector: 'node[status = "mastered"]',
                    style: {
                        'background-color': '#00fa9a',
                        'border-color': '#00b894',
                        'color': '#000',
                        'font-weight': '700'
                    }
                }
            ]
        });

        console.log("🕸️ Graph Module Initialized Success");
    },

    loadData: async function () {
        if (!this.cy) return;

        try {
            console.log("🕸️ Fetching Graph Data...");
            const response = await fetch('/api/kb/graph');
            const data = await response.json();

            // Clear and add
            this.cy.elements().remove();

            if (!data.elements || data.elements.length === 0) {
                console.warn("⚠️ No graph elements returned from API");
                // Add dummy node to prove rendering works if API empty
                this.cy.add([
                    { group: 'nodes', data: { id: 'dummy', label: 'Empty Knowledge Base', status: 'pending' } }
                ]);
                this.cy.center();
                return;
            }

            this.cy.add(data.elements);

            // Layout
            const layout = this.cy.layout({
                name: 'dagre',
                rankDir: 'TB',
                spacingFactor: 1.2,
                padding: 30,
                animate: true,
                animationDuration: 500
            });
            layout.run();

            // Center
            setTimeout(() => {
                this.cy.fit();
                this.cy.center();
            }, 600);

            console.log("✅ Graph Rendered with elements:", data.elements.length);
        } catch (e) {
            console.error("❌ Graph Load Fail", e);
        }
    }
};
