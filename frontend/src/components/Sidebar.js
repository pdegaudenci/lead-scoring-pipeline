import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react'; // o texto si no usas íconos

function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className={`bg-gray-800 text-white transition-all duration-300 ${isOpen ? 'w-64' : 'w-16'} min-h-screen`}>
      <div className="p-4 flex flex-col">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="mb-4 text-white hover:text-yellow-300"
        >
          {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>

        {isOpen && (
          <>
            <h2 className="text-xl font-bold mb-6">Lead Dashboard</h2>
            <ul>
              <li className="mb-4">
                <Link to="/charts" className="hover:text-yellow-300">📊 Gráficos</Link>
              </li>
              <li className="mb-4">
                <Link to="/table" className="hover:text-yellow-300">📋 Tabla</Link>
              </li>
              <li>
                <Link to="/scoring" className="hover:text-yellow-300">🧠 Scoring</Link>
              </li>
              <li className="mb-4">
                <Link to="/upload" className="hover:text-yellow-300">⬆️ Subir Archivos</Link>
              </li>
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

export default Sidebar;
