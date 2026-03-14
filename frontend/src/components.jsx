"""
TalkToMe Frontend - React App Structure
Package.json and main components
"""

# File: frontend/package.json

{
  "name": "talktome-frontend",
  "version": "1.0.0",
  "description": "Anonymous feedback platform",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.3.0",
    "chart.js": "^3.9.1",
    "react-chartjs-2": "^4.3.1",
    "recharts": "^2.5.0",
    "tailwindcss": "^3.2.4",
    "react-icons": "^4.7.1",
    "react-hot-toast": "^2.4.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": ["react-app"]
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version"]
  }
}


---

# File: frontend/src/App.jsx

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navigation from './components/Navigation';
import LeaderDashboard from './pages/LeaderDashboard';
import FeedbackForm from './pages/FeedbackForm';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import Register from './pages/Register';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('leader_id'));
  
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation isLoggedIn={isLoggedIn} setIsLoggedIn={setIsLoggedIn} />
        
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<LeaderDashboard />} />
            <Route path="/feedback/:uid" element={<FeedbackForm />} />
            <Route path="/analytics/:sessionId" element={<Analytics />} />
            <Route path="/login" element={<Login setIsLoggedIn={setIsLoggedIn} />} />
            <Route path="/register" element={<Register setIsLoggedIn={setIsLoggedIn} />} />
          </Routes>
        </main>
        
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;


---

# File: frontend/src/pages/FeedbackForm.jsx

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import { FiSend, FiCheckCircle } from 'react-icons/fi';

function FeedbackForm() {
  const { uid } = useParams();
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!content.trim()) {
      toast.error('Please write your feedback');
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post('http://localhost:5000/api/feedback/submit', {
        uid,
        content
      });
      
      toast.success('Thank you! Your feedback has been submitted anonymously');
      setSubmitted(true);
      setContent('');
      
      setTimeout(() => setSubmitted(false), 3000);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Share Your Feedback</h1>
        <p className="text-gray-600 mb-6">
          Your feedback is valuable and completely anonymous. 
          Your identity will never be revealed to the leader.
        </p>
        
        {submitted && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
            <FiCheckCircle className="text-green-600 text-2xl" />
            <div>
              <p className="font-semibold text-green-800">Feedback Submitted</p>
              <p className="text-green-700 text-sm">Thank you for your honest feedback!</p>
            </div>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Your Feedback
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Share your thoughts, concerns, suggestions, or any feedback..."
              rows="8"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              disabled={loading}
            />
            <p className="text-gray-500 text-sm mt-2">
              Minimum 10 characters recommended
            </p>
          </div>
          
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition disabled:opacity-50"
            >
              <FiSend /> Submit Feedback
            </button>
          </div>
        </form>
        
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="font-semibold text-gray-800 mb-3">Privacy Assurance</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Completely anonymous - your identity is never stored</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Leader cannot see raw feedback - only AI-generated insights</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>No tracking of IP address or device information</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>All data is encrypted and securely stored</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default FeedbackForm;


---

# File: frontend/src/pages/Analytics.jsx

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { FiRefreshCw, FiDownload } from 'react-icons/fi';

function Analytics() {
  const { sessionId } = useParams();
  const [analytics, setAnalytics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const COLORS = ['#10b981', '#f3f4f6', '#ef4444'];
  
  useEffect(() => {
    fetchAnalytics();
  }, [sessionId]);
  
  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const leaderId = localStorage.getItem('leader_id');
      if (!leaderId) {
        toast.error('Please login first');
        return;
      }
      
      const [analyticsRes, trendsRes] = await Promise.all([
        axios.get(`http://localhost:5000/api/sessions/${sessionId}/analytics`, {
          headers: { 'X-Leader-ID': leaderId }
        }),
        axios.get(`http://localhost:5000/api/sessions/${sessionId}/trends`, {
          headers: { 'X-Leader-ID': leaderId }
        })
      ]);
      
      setAnalytics(analyticsRes.data);
      
      // Convert trends to chart data
      const trendData = Object.entries(trendsRes.data.trends || {}).map(([date, score]) => ({
        date,
        satisfaction: score
      }));
      setTrends(trendData);
    } catch (err) {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin text-4xl">⏳</div>
      </div>
    );
  }
  
  if (!analytics) {
    return <div className="text-center text-gray-600">No analytics available</div>;
  }
  
  const sentimentData = [
    { name: 'Positive', value: analytics.sentiment.positive },
    { name: 'Neutral', value: analytics.sentiment.neutral },
    { name: 'Negative', value: analytics.sentiment.negative }
  ];
  
  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Feedback Analytics</h1>
        <button
          onClick={fetchAnalytics}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
        >
          <FiRefreshCw /> Refresh
        </button>
      </div>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-semibold">Total Feedbacks</p>
          <p className="text-4xl font-bold text-gray-800">{analytics.total_feedbacks}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-semibold">Satisfaction Score</p>
          <p className="text-4xl font-bold text-green-600">{analytics.satisfaction_score}/10</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm font-semibold">Last Updated</p>
          <p className="text-sm text-gray-700">{new Date(analytics.updated_at).toLocaleDateString()}</p>
        </div>
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Sentiment Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Sentiment Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        {/* Trends Line Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Satisfaction Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="satisfaction"
                stroke="#3b82f6"
                dot={false}
                name="Satisfaction"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Top Issues */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Issues & Themes</h3>
        <div className="space-y-3">
          {analytics.top_issues?.map((issue, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span className="text-gray-700">{issue.issue}</span>
              <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-semibold">
                {issue.percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Executive Summary</h3>
        <p className="text-gray-700 leading-relaxed">{analytics.summary}</p>
      </div>
      
      {/* Export Button */}
      <button className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition">
        <FiDownload /> Export Report
      </button>
    </div>
  );
}

export default Analytics;
