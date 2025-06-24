import React from 'react';
import { Pie } from 'react-chartjs-2';

function LeadSourceChart({ leads }) {
    const sourceData = leads.reduce((acc, lead) => {
        const source = lead.Lead_Source || 'Unknown';
        acc[source] = (acc[source] || 0) + 1;
        return acc;
    }, {});

    const data = {
        labels: Object.keys(sourceData),
        datasets: [
            {
                label: 'Lead Source',
                data: Object.values(sourceData),
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(153, 102, 255, 0.6)',
                    'rgba(255, 159, 64, 0.6)',
                    'rgba(201, 203, 207, 0.6)',
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(201, 203, 207, 1)',
                ],
                borderWidth: 1,
            },
        ],
    };

    return <Pie data={data} />;
}

export default LeadSourceChart;
