import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const MetricCard = ({ title, data }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-center">
    <h3 className="text-gray-500 text-sm font-medium mb-2">{title}</h3>
    <p className="text-3xl font-bold text-blue-600">{data.value}</p>
  </div>
);

const CustomBarChart = ({ title, data }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 h-80">
    <h3 className="text-gray-500 text-sm font-medium mb-4">{title}</h3>
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <XAxis dataKey="name" tick={{fontSize: 12}} />
        <YAxis tick={{fontSize: 12}} width={80} />
        <Tooltip cursor={{fill: '#f3f4f6'}} />
        <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
);

const CustomPieChart = ({ title, data }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 h-80 flex flex-col">
    <h3 className="text-gray-500 text-sm font-medium mb-4">{title}</h3>
    <div className="flex-1">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value" label={({name}) => name}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  </div>
);

const ProductList = ({ title, data }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 h-80 overflow-y-auto">
    <h3 className="text-gray-500 text-sm font-medium mb-4">{title}</h3>
    <ul className="divide-y divide-gray-100">
      {data.map((item, idx) => (
        <li key={idx} className="py-3 flex justify-between items-center">
          <span className="text-sm text-gray-700 truncate pr-4">{item.name}</span>
          <span className="text-sm font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{item.value} шт.</span>
        </li>
      ))}
    </ul>
  </div>
);

// --- ФАБРИКА ВИДЖЕТОВ ---
const WidgetFactory = ({ config }) => {
  switch (config.type) {
    case 'MetricCard':
      return <MetricCard title={config.title} data={config.data} />;
    case 'BarChart':
      return <CustomBarChart title={config.title} data={config.data} />;
    case 'PieChart':
      return <CustomPieChart title={config.title} data={config.data} />;
    case 'ProductList':
      return <ProductList title={config.title} data={config.data} />;
    default:
      return <div className="p-4 bg-red-100 text-red-500 rounded">Unknown Widget: {config.type}</div>;
  }
};


// --- ГЛАВНАЯ СТРАНИЦА ---
export default function App() {
  const [widgets, setWidgets] = useState([]);
  const [loading, setLoading] = useState(true);

  const API_URL = import.meta.env.DEV ? 'http://127.0.0.1:8000' : '';

  useEffect(() => {
    fetch(`${API_URL}/api/dashboard`)
      .then(res => res.json())
      .then(data => {
        setWidgets(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Ошибка загрузки:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="animate-pulse text-gray-500 text-xl font-medium">Загрузка дашборда...</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 border-b border-gray-200 pb-4">
          <h1 className="text-3xl font-bold text-gray-800">Аналитика RetailCRM</h1>
          <p className="text-gray-500 text-sm mt-1">Отчет по продажам, товарам и трафику</p>
        </header>
        
        {/* Рендерим виджеты. Добавлена логика masonry / grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {widgets.filter(w => w.type === 'MetricCard').map(widget => (
            <WidgetFactory key={widget.id} config={widget} />
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {widgets.filter(w => w.type !== 'MetricCard').map(widget => (
            <div key={widget.id} className={widget.type === 'BarChart' ? "lg:col-span-2" : ""}>
               <WidgetFactory config={widget} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
