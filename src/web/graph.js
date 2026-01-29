const Graph = {
    cy: null,
    pulseAnimation: null,

    init: function () {
        console.log("🕸️ Graph.init() - BreadthFirst Edition");
        const container = document.getElementById('cy');
        if (!container) return;

        container.style.border = "none";

        try {
            this.cy = cytoscape({
                container: container,
                wheelSensitivity: 0.2,
                maxZoom: 2.5,
                minZoom: 0.5,
                style: [
                    // NODE DEFAULTS
                    {
                        selector: 'node',
                        style: {
                            'background-color': '#2d3436',
                            'label': 'data(label)',
                            'color': '#dfe6e9',
                            'font-size': '16px',
                            'font-family': 'Outfit, sans-serif',
                            'font-weight': '500',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'width': 'label',
                            'padding': '16px',
                            'shape': 'round-rectangle',
                            'border-width': 1,
                            'border-color': '#636e72',
                            'text-wrap': 'wrap',
                            'text-max-width': '140px',
                            'transition-property': 'background-color, border-color, shadow-blur',
                            'transition-duration': '0.3s'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 3,
                            'line-color': '#636e72',
                            'curve-style': 'taxi',
                            'taxi-direction': 'downward',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-color': '#636e72',
                            'arrow-scale': 1.5
                        }
                    },
                    // --- STATES ---
                    {
                        selector: 'node[status = "active"]',
                        style: {
                            'background-color': '#6c5ce7',
                            'border-color': '#a29bfe',
                            'color': '#fff',
                            'border-width': 2,
                            'shadow-blur': 25,
                            'shadow-color': '#6c5ce7',
                            'font-weight': '700'
                        }
                    },
                    {
                        selector: 'node[status = "mastered"]',
                        style: {
                            'background-color': '#00b894',
                            'border-color': '#55efc4',
                            'color': '#fff',
                            'border-width': 1,
                            'shadow-blur': 10,
                            'shadow-color': '#00b894'
                        }
                    },
                    {
                        selector: 'node[status = "pending"]',
                        style: { 'opacity': 0.8 }
                    }
                ]
            });
            console.log("Cytoscape instance created.");
        } catch (e) {
            console.error("Cytoscape init failed:", e);
        }
    },

    loadData: async function () {
        if (!this.cy) return;

        try {
            this.stopPulse();

            const response = await fetch('/api/kb/graph');
            const data = await response.json();

            this.cy.elements().remove();

            if (!data.elements || data.elements.length === 0) {
                this.cy.add([
                    { group: 'nodes', data: { id: 'dummy', label: 'Empty Topic', status: 'pending' } }
                ]);
            } else {
                this.cy.add(data.elements);
            }

            // NATIVE LAYOUT FALLBACK
            setTimeout(() => {
                const layout = this.cy.layout({
                    name: 'breadthfirst', // Native, reliable
                    directed: true,
                    padding: 40,
                    spacingFactor: 1.5,   // Space out nodes
                    animate: true,
                    animationDuration: 800,
                    stop: () => {
                        this.startPulse();
                    }
                });
                layout.run();
                console.log("Layout: Breadthfirst executed");
            }, 50);

        } catch (e) {
            console.error("❌ Graph Load Fail", e);
        }
    },

    startPulse: function () {
        const activeNode = this.cy.nodes('[status = "active"]');
        if (activeNode.length === 0) return;

        const animate = () => {
            activeNode.animation({
                style: { 'shadow-blur': 40, 'border-width': 4 },
                duration: 800
            }).play().promise().then(() => {
                return activeNode.animation({
                    style: { 'shadow-blur': 20, 'border-width': 2 },
                    duration: 800
                }).play().promise();
            }).then(animate);
        };
        this.pulseAnimation = animate();
    },

    stopPulse: function () {
        if (this.cy) this.cy.stop(true);
    }
};

window.Graph = Graph;
