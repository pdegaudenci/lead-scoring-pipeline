import React from 'react';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Title,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Registrar componentes de Chart.js (solo una vez en tu app)
ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Title
);

function LeadActivityChart({ leads }) {
  const activityData = leads.reduce((acc, lead) => {
    const lastActivity = lead.Last_Activity || 'Unknown';
    acc[lastActivity] = (acc[lastActivity] || 0) + 1;
    return acc;
  }, {});

  const data = {
    labels: Object.keys(activityData),
    datasets: [
      {
        label: 'Lead Activity',
        data: Object.values(activityData),
        fill: false,
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Lead Activity Over Time',
      },
    },
  };

  return <Line data={data} options={options} />;
}

export default LeadActivityChart;
