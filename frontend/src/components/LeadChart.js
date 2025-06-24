// src/components/LeadChart.js
import React from 'react';
import {
    Chart as ChartJS,
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Registrar los elementos de Chart.js
ChartJS.register(
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement
);

function LeadChart({ leads }) {
    const labels = leads.map(lead => lead.Name || `Lead`);
    const scores = leads.map(lead => lead.Lead_Score || 0);

    const data = {
        labels,
        datasets: [
            {
                label: 'Lead Scores',
                data: scores,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }
        ]
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Lead Scores',
            },
        },
    };

    return <Bar data={data} options={options} />;
}

export default LeadChart;
