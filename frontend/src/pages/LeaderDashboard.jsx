"""
TalkToMe React Components - Leader Dashboard
"""

// File: frontend/src/pages/LeaderDashboard.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import { FiPlus, FiCopy, FiGlobe, FiClock, FiUsers } from 'react-icons/fi';

function LeaderDashboard() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    deadline: '',
    allow_multiple_submissions: true,
    require_email: false
  });
  
  const leaderId = localStorage.getItem('leader_id');
  
  useEffect(() => {
    if (!leaderId) {
      navigate('/login');
      return;
    }
    fetchSessions();
  }, [leaderId]);
  
  const fetchSessions = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:5000/api/sessions', {
        headers: { 'X-Leader-ID': leaderId }
      });
      setSessions(res.data.sessions);
    } catch (err) {
      toast.error('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };
  
  const handleCreateSession = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      toast.error('Title is required');
      return;
    }
    
    try {
      const res = await axios.post('http://localhost:5000/api/sessions', 
        formData,
        { headers: { 'X-Leader-ID': leaderId } }
      );
      
      toast.success('Feedback session created!');
      setFormData({
        title: '',
        description: '',
        deadline: '',
        allow_multiple_submissions: true,
        require_email: false
      });
      setShowCreateModal(false);
      
      fetchSessions();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create session');
    }
  };
  
  const copyUID = (uid) => {
    navigator.clipboard.writeText(uid);
    toast.success('UID copied to clipboard!');
  };
  
  const handleOpenAnalytics = (sessionId) => {
    navigate(`/analytics/${sessionId}`);
  };
  
  const handleCloseSession = async (sessionId) => {
    if (!window.confirm('Are you sure? This cannot be undone.')) return;
    
    try {
      await axios.post(
        `http://localhost:5000/api/sessions/${sessionId}/close`,
        {},
        { headers: { 'X-Leader-ID': leaderId } }
      );
      
      toast.success('Session closed');
      fetchSessions();
    } catch (err) {
      toast.error('Failed to close session');
    }
  };
  
  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold text-gray-800">Feedback Sessions</h1>
          <p className="text-gray-600 mt-2">Create and manage anonymous feedback collections</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
        >
          <FiPlus /> New Session
        </button>
      </div>
      
      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Create Feedback Session</h2>
            
            <form onSubmit={handleCreateSession} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  placeholder="Q1 Team Feedback"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Brief description of feedback topic..."
                  rows="3"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Deadline</label>
                <input
                  type="datetime-local"
                  value={formData.deadline}
                  onChange={(e) => setFormData({...formData, deadline: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.allow_multiple_submissions}
                    onChange={(e) => setFormData({...formData, allow_multiple_submissions: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-700">Allow multiple submissions per person</span>
                </label>
                
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.require_email}
                    onChange={(e) => setFormData({...formData, require_email: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-700">Require email (for follow-up)</span>
                </label>
              </div>
              
              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Sessions List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin text-4xl">⏳</div>
        </div>
      ) : sessions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-600 text-lg">No feedback sessions yet</p>
          <p className="text-gray-500">Create your first session to start collecting feedback</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {sessions.map((session) => (
            <div key={session.id} className="bg-white rounded-lg shadow hover:shadow-lg transition p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-800">{session.title}</h3>
                  <p className="text-gray-600 text-sm mt-1">
                    Created {new Date(session.created_at).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    session.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                  </span>
                </div>
              </div>
              
              {/* UID Code Box */}
              <div className="bg-gray-50 rounded p-4 mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 font-semibold uppercase">Feedback Code</p>
                  <p className="text-2xl font-mono font-bold text-blue-600">{session.uid}</p>
                </div>
                <button
                  onClick={() => copyUID(session.uid)}
                  className="p-2 hover:bg-gray-200 rounded transition"
                >
                  <FiCopy className="text-gray-600" />
                </button>
              </div>
              
              {/* Metrics */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <FiUsers className="mx-auto text-gray-400 mb-1 text-xl" />
                  <p className="text-2xl font-bold text-gray-800">{session.feedbacks_count}</p>
                  <p className="text-xs text-gray-600">Feedbacks</p>
                </div>
                <div className="text-center">
                  <FiGlobe className="mx-auto text-gray-400 mb-1 text-xl" />
                  <p className="text-2xl font-bold text-gray-800">
                    {session.satisfaction_score ? session.satisfaction_score.toFixed(1) : '-'}
                  </p>
                  <p className="text-xs text-gray-600">Satisfaction</p>
                </div>
                <div className="text-center">
                  <FiClock className="mx-auto text-gray-400 mb-1 text-xl" />
                  <p className="text-sm text-gray-800 font-semibold">
                    {session.deadline ? new Date(session.deadline).toLocaleDateString() : 'No deadline'}
                  </p>
                  <p className="text-xs text-gray-600">Deadline</p>
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={() => handleOpenAnalytics(session.id)}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-semibold"
                >
                  View Analytics
                </button>
                
                {session.status === 'active' && (
                  <button
                    onClick={() => handleCloseSession(session.id)}
                    className="px-4 py-2 border border-red-300 text-red-600 hover:bg-red-50 rounded-lg transition"
                  >
                    Close
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default LeaderDashboard;
