
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function LeadChart({ leads }) {
    if (!leads.length) return <p>Cargando gráfico...</p>;

    // Asumir que hay una columna "Lead_Score" en los datos
    const chartData = leads.map((lead, index) => ({
        name: `Lead ${index + 1}`,
        score: parseInt(lead.Lead_Score) || 0
    }));

    return (
        <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Puntuación de Leads</h2>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="score" fill="#8884d8" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

export default LeadChart;
