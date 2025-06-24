import React from 'react';
import { Bar } from 'react-chartjs-2';

function LeadConversionChart({ leads }) {
    const conversionData = leads.reduce((acc, lead) => {
        const stage = lead.Lead_Stage || 'Unknown';
        acc[stage] = (acc[stage] || 0) + 1;
        return acc;
    }, {});

    const data = {
        labels: Object.keys(conversionData),
        datasets: [
            {
                label: 'Lead Conversion',
                data: Object.values(conversionData),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
            },
        ],
    };

    return <Bar data={data} />;
}

export default LeadConversionChart;
