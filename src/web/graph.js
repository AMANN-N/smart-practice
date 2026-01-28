const Graph = {
    cy: null,

    init: function () {
        this.cy = cytoscape({
            container: document.getElementById('cy'),
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#2a2a3b',
                        'label': 'data(label)',
                        'color': '#a0a0b0',
                        'font-size': '12px',
                        'font-family': 'Outfit',
                        'text-valign': 'bottom',
                        'text-margin-y': 5,
                        'width': 25,
                        'height': 25,
                        'border-width': 2,
                        'border-color': '#555'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#444',
                        'curve-style': 'taxi', /* Taxi style for tree lines */
                        'taxi-direction': 'downward',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#444'
                    }
                },
                // Active (Current Focus)
                {
                    selector: 'node[status = "active"]',
                    style: {
                        'background-color': '#646cff', // Primary
                        'border-color': '#fff',
                        'width': 40,
                        'height': 40,
                        'font-size': '14px',
                        'font-weight': 'bold',
                        'color': '#fff',
                        'shadow-blur': 25,
                        'shadow-color': '#646cff'
                    }
                },
                // Mastered
                {
                    selector: 'node[status = "mastered"]',
                    style: {
                        'background-color': '#00fa9a', // Success
                        'border-color': '#00fa9a',
                        'shadow-blur': 15,
                        'shadow-color': '#00fa9a'
                    }
                }
            ]
        });
    },

    loadData: async function () {
        try {
            const response = await fetch('/api/kb/graph');
            const data = await response.json();

            this.cy.elements().remove();
            this.cy.add(data.elements);

            // Tree Layout
            const layout = this.cy.layout({
                name: 'dagre',
                rankDir: 'TB', // Top-to-Bottom
                spacingFactor: 1.2,
                animate: true,
                animationDuration: 500,
                fit: true,
                padding: 30
            });
            layout.run();
        } catch (e) {
            console.error("Graph Load Fail", e);
        }
    },

    highlightNode: function (nodeId) {
        if (!this.cy) return;
        this.cy.zoom({
            level: 1.5,
            position: this.cy.$id(nodeId).position()
        });
    }
};
