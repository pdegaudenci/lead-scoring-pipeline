
import React from 'react';

function LeadTable({ leads }) {
    if (!leads.length) return <p>Cargando datos...</p>;

    const columns = Object.keys(leads[0]);

    return (
        <table className="table-auto w-full border-collapse border border-gray-300">
            <thead>
                <tr>
                    {columns.map((col, index) => (
                        <th key={index} className="border px-4 py-2 bg-gray-100">{col}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {leads.map((lead, index) => (
                    <tr key={index} className="hover:bg-gray-100">
                        {columns.map((col, idx) => (
                            <td key={idx} className="border px-4 py-2">{lead[col]}</td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export default LeadTable;
