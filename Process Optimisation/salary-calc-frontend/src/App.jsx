import React, { useState } from 'react';
import { Plus, Save, Trash2 } from 'lucide-react';

const initialColumns = [
  "S No",
  "UAN No",
  "Name of Employee",
  "Designation",
  "Emp ID",
  "Department",
  "ESIC No",
  "PAN No",
  "Aadhaar No",
  "Bank",
  "IFSC Code",
  "Account No.",
  "PF Eligible (Y/N)",
  "ENPF/VPF",
  "Pension Eligible (Y/N)",
  "ESIC Eligible (Y/N)"
];

function App() {
  const [employees, setEmployees] = useState([
    Array(initialColumns.length).fill('')
  ]);

  const handleAddRow = () => {
    setEmployees([...employees, Array(initialColumns.length).fill('')]);
  };

  const handleCellChange = (rowIndex, colIndex, value) => {
    const updated = [...employees];
    updated[rowIndex][colIndex] = value;
    setEmployees(updated);
  };

  const handleRemoveRow = (index) => {
    const updated = employees.filter((_, i) => i !== index);
    setEmployees(updated);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-800">
      <header className="mb-8 max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
          Salary Calculator Portal
        </h1>
        <p className="text-slate-500 mt-2">Manage employee data securely.</p>
      </header>

      <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
          <div>
            <h2 className="text-xl font-semibold text-slate-800">Employee Directory</h2>
            <p className="text-sm text-slate-500 mt-1">Add or compile employee salary parameters manually.</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={handleAddRow}
              className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-2 text-sm font-medium"
            >
              <Plus size={16} /> Add Row
            </button>
            <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-200 flex items-center gap-2 text-sm font-medium">
              <Save size={16} /> Save Data
            </button>
          </div>
        </div>

        <div className="overflow-x-auto h-[60vh]">
          <table className="w-full text-left border-collapse min-w-max relative">
            <thead className="sticky top-0 z-10 shadow-sm">
              <tr className="bg-slate-50 border-b border-slate-200">
                {initialColumns.map((col, idx) => (
                  <th key={idx} className="p-3 text-xs font-semibold tracking-wider text-slate-600 uppercase whitespace-nowrap bg-slate-50">
                    {col}
                  </th>
                ))}
                <th className="p-3 w-10 bg-slate-50"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {employees.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-slate-50/50 transition-colors group">
                  {row.map((cell, colIndex) => (
                    <td key={colIndex} className="p-1 min-w-[120px]">
                      <input
                        type="text"
                        value={cell}
                        onChange={(e) => handleCellChange(rowIndex, colIndex, e.target.value)}
                        className="w-full p-2 bg-transparent border border-transparent rounded focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                        placeholder="—"
                      />
                    </td>
                  ))}
                  <td className="p-2 text-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => handleRemoveRow(rowIndex)}
                      className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Remove row"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
              {employees.length === 0 && (
                <tr>
                  <td colSpan={initialColumns.length + 1} className="p-12 text-center text-slate-500 italic">
                    No employees added. Click "Add Row" to start adding data.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
