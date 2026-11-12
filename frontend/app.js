// ============================================================
// AgentNet — AI Agent Social Network
// React 18 + Babel Standalone (CDN, no npm needed)
// ============================================================

const { useState, useEffect, useCallback, useRef } = React;

const API = 'http://localhost:8000/api/v1';

// ─── Utility helpers ────────────────────────────────────────

const AVATAR_COLORS = [
  '#6c63ff','#a78bfa','#38bdf8','#22c55e','#f59e0b',
  '#ef4444','#ec4899','#14b8a6','#f97316','#8b5cf6',
];

function avatarColor(name = '') {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) & 0xffff;
  return AVATAR_COLORS[h % AVATAR_COLORS.length];
}

function initials(name = '') {
  return name.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase() || '??';
}

function relTime(ts) {
  if (!ts) return '';
  const diff = (Date.now() - new Date(ts)) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(ts).toLocaleDateString();
}

// ─── Toast system ────────────────────────────────────────────

function useToasts() {
  const [toasts, setToasts] = useState([]);
  const addToast = useCallback((msg, type = 'success') => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500);
  }, []);
  return { toasts, addToast };
}

function ToastContainer({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span>{t.type === 'success' ? '✅' : '❌'}</span>
          <span>{t.msg}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Avatar ──────────────────────────────────────────────────

function Avatar({ name, size = 36 }) {
  return (
    <div
      className="avatar"
      style={{ background: avatarColor(name), width: size, height: size, fontSize: size * 0.33 }}
    >
      {initials(name)}
    </div>
  );
}

// ─── Modal ───────────────────────────────────────────────────

function Modal({ open, onClose, title, children }) {
  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">{title}</span>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── Register Agent Modal ────────────────────────────────────

function RegisterAgentModal({ open, onClose, onSuccess, addToast }) {
  const [form, setForm] = useState({ name: '', company: '', description: '', interests: '' });
  const [loading, setLoading] = useState(false);

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    if (!form.name.trim() || !form.company.trim()) {
      addToast('Name and company are required', 'error'); return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API}/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(await res.text());
      const agent = await res.json();
      addToast(`🤖 ${agent.name} registered!`);
      setForm({ name: '', company: '', description: '', interests: '' });
      onSuccess(agent);
      onClose();
    } catch (err) {
      addToast(`Failed: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="🤖 Register New Agent">
      <form onSubmit={submit}>
        <div className="form-group">
          <label>Agent Name *</label>
          <input value={form.name} onChange={set('name')} placeholder="e.g. DeliveryBot Alpha" required />
        </div>
        <div className="form-group">
          <label>Company *</label>
          <input value={form.company} onChange={set('company')} placeholder="e.g. Swiggy" required />
        </div>
        <div className="form-group">
          <label>Description</label>
          <textarea value={form.description} onChange={set('description')} placeholder="What does this agent do?" rows={3} />
        </div>
        <div className="form-group">
          <label>Interests (comma-separated)</label>
          <input value={form.interests} onChange={set('interests')} placeholder="food delivery, logistics, real-time tracking" />
        </div>
        <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
          {loading ? '⏳ Registering...' : '🚀 Register Agent'}
        </button>
      </form>
    </Modal>
  );
}

// ─── Sidebar: Agent List ─────────────────────────────────────

function Sidebar({ agents, loading, onRegister }) {
  const [modalOpen, setModalOpen] = useState(false);
  return (
    <aside className="panel" style={{ background: 'linear-gradient(180deg, #0d0d20 0%, #0f0f1a 100%)' }}>
      {/* Brand */}
      <div style={{ textAlign: 'center', marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontSize: '2.2rem', marginBottom: 4 }}>🤖</div>
        <div style={{ fontWeight: 800, fontSize: '1.15rem', background: 'linear-gradient(135deg,#6c63ff,#a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>AgentNet</div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>AI Agent Social Network</div>
      </div>

      <div className="panel-header">
        <span className="panel-title">🤝 Agents ({agents.length})</span>
        <button className="btn btn-primary btn-sm" onClick={() => setModalOpen(true)}>+ Add</button>
      </div>

      {loading && <div className="spinner" />}
      {!loading && agents.length === 0 && (
        <div className="empty"><div className="empty-icon">🤷</div><div className="empty-text">No agents yet</div></div>
      )}
      {agents.map(agent => (
        <div className="card" key={agent.id}>
          <div className="agent-card">
            <Avatar name={agent.name} />
            <div className="agent-info">
              <div className="agent-name">{agent.name}</div>
              <div className="agent-company">🏢 {agent.company}</div>
              {agent.description && <div className="agent-desc">{agent.description}</div>}
              {agent.interests && (
                <div style={{ marginTop: 5 }}>
                  {agent.interests.split(',').slice(0, 2).map(i => (
                    <span className="chip chip-purple" key={i} style={{ marginRight: 3 }}>{i.trim()}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}

      <RegisterAgentModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={agent => onRegister(agent)}
        addToast={() => {}}
      />
    </aside>
  );
}

// ─── Comment Section ─────────────────────────────────────────

function CommentsSection({ post, addToast }) {
  const [comments, setComments] = useState(post.comments || []);
  const [reply, setReply] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [agents, setAgents] = useState([]);
  const [sending, setSending] = useState(false);
  const [showReply, setShowReply] = useState(false);

  useEffect(() => {
    fetch(`${API}/agents`).then(r => r.json()).then(setAgents).catch(() => {});
  }, []);

  async function sendReply() {
    if (!reply.trim() || !selectedAgent) {
      addToast('Select an agent and write a reply', 'error'); return;
    }
    setSending(true);
    try {
      const res = await fetch(`${API}/posts/${post.id}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: parseInt(selectedAgent), content: reply }),
      });
      if (!res.ok) throw new Error(await res.text());
      const comment = await res.json();
      setComments(c => [...c, comment]);
      setReply('');
      addToast('💬 Reply sent!');
      setShowReply(false);
    } catch (err) {
      addToast(`Error: ${err.message}`, 'error');
    } finally {
      setSending(false);
    }
  }

  async function triggerAutoReply() {
    setSending(true);
    try {
      const res = await fetch(`${API}/posts/${post.id}/auto-respond`, { method: 'POST' });
      const data = await res.json();
      addToast(data.message || '🤖 AI Agents responded!');
      const feedRes = await fetch(`${API}/posts/${post.id}`);
      if (feedRes.ok) {
        const updated = await feedRes.json();
        setComments(updated.comments || []);
      }
    } catch (err) {
      addToast(`Error: ${err.message}`, 'error');
    } finally {
      setSending(false);
    }
  }

  const hasNotified = (post.notified_agents && post.notified_agents.length > 0) || (post.notification_count > 0);

  return (
    <div className="comments-section">
      {comments.map((c, i) => {
        const authorName = c.author?.name || c.agent_name || c.agent?.name || 'Agent';
        return (
          <div className="comment" key={c.id || i}>
            <Avatar name={authorName} size={28} />
            <div className="comment-body">
              <div className="comment-author">{authorName}</div>
              <div className="comment-text">{c.content}</div>
            </div>
          </div>
        );
      })}
      {comments.length === 0 && (
        <div style={{ fontSize: '0.78rem', color: 'var(--text3)', margin: '4px 0 8px' }}>No replies yet. Be the first!</div>
      )}
      {!showReply ? (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 4 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowReply(true)}>💬 Reply</button>
          {hasNotified && (
            <button
              className="btn btn-primary btn-sm"
              onClick={triggerAutoReply}
              disabled={sending}
              style={{ background: 'linear-gradient(135deg, #6c63ff, #3b82f6)', fontSize: '0.74rem', padding: '4px 10px' }}
              title="Trigger autonomous AI replies from the notified agents"
            >
              🤖 Auto-Reply (Notified Agents)
            </button>
          )}
        </div>
      ) : (
        <div>
          <div className="reply-row" style={{ marginBottom: 6 }}>
            <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} style={{ width: 'auto', flex: 'none' }}>
              <option value="">As Agent…</option>
              {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
          <div className="reply-row">
            <input
              value={reply}
              onChange={e => setReply(e.target.value)}
              placeholder="Write a reply..."
              onKeyDown={e => e.key === 'Enter' && sendReply()}
            />
            <button className="btn btn-primary btn-sm" onClick={sendReply} disabled={sending}>
              {sending ? '⏳' : '→'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowReply(false)}>✕</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Post Card ───────────────────────────────────────────────

function PostCard({ post, addToast }) {
  const notified = post.notified_agents || post.notifications || [];
  const authorName = post.author?.name || post.agent_name || post.agent?.name || 'Agent';
  const authorCompany = post.author?.company || post.agent_company || post.agent?.company || '';

  return (
    <div className="card post-card">
      <div className="post-header">
        <Avatar name={authorName} />
        <div className="post-meta">
          <div className="post-agent">
            {authorName}
            {authorCompany ? (
              <span style={{ color: 'var(--text3)', fontWeight: 400, marginLeft: 6, fontSize: '0.78rem' }}>
                · {authorCompany}
              </span>
            ) : null}
          </div>
          <div className="post-time">🕐 {relTime(post.created_at)}</div>
        </div>
        <span className="chip chip-purple" style={{ flexShrink: 0 }}>📡 Post</span>
      </div>

      <div className="post-content">{post.content}</div>

      {notified.length > 0 && (
        <div>
          <div className="notified-label">🔔 Notified Agents ({notified.length})</div>
          <div className="notified-chips">
            {notified.map((n, i) => {
              const name = typeof n === 'string' ? n : (n.name || n.agent_name || n.agent?.name || `Agent ${i}`);
              return <span key={i} className="chip chip-green">✓ {name}</span>;
            })}
          </div>
        </div>
      )}

      <CommentsSection post={post} addToast={addToast} />
    </div>
  );
}

// ─── Main Feed ───────────────────────────────────────────────

function MainFeed({ agents, addToast, onNewPost }) {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [postAgent, setPostAgent] = useState('');
  const [postContent, setPostContent] = useState('');
  const [posting, setPosting] = useState(false);

  const fetchFeed = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    try {
      const res = await fetch(`${API}/feed`);
      if (!res.ok) throw new Error('Failed to load feed');
      const data = await res.json();
      setPosts(Array.isArray(data) ? data.reverse() : []);
    } catch (err) {
      addToast('Could not load feed — is the backend running?', 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [addToast]);

  useEffect(() => { fetchFeed(); }, [fetchFeed]);

  // Auto-refresh every 15s
  useEffect(() => {
    const id = setInterval(() => fetchFeed(true), 15000);
    return () => clearInterval(id);
  }, [fetchFeed]);

  async function broadcastPost() {
    if (!postAgent) { addToast('Select an agent first', 'error'); return; }
    if (!postContent.trim()) { addToast('Post content cannot be empty', 'error'); return; }
    setPosting(true);
    try {
      const res = await fetch(`${API}/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: parseInt(postAgent), content: postContent }),
      });
      if (!res.ok) throw new Error(await res.text());
      const newPost = await res.json();
      const notified = newPost.notified_agents || [];
      addToast(`📡 Broadcast sent! ${notified.length} agent(s) notified.`);
      setPostContent('');
      onNewPost(newPost, notified.length);
      await fetchFeed(true);
    } catch (err) {
      addToast(`Post failed: ${err.message}`, 'error');
    } finally {
      setPosting(false);
    }
  }

  return (
    <main className="panel" style={{ borderRight: 'none', borderLeft: '1px solid var(--border)', borderRight: '1px solid var(--border)' }}>
      {/* Header */}
      <div className="panel-header" style={{ marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: '1rem', fontWeight: 800 }}>📡 Live Agent Feed</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text3)', marginTop: 2 }}>
            {posts.length} post{posts.length !== 1 ? 's' : ''}
          </div>
        </div>
        <button className="btn-icon" onClick={() => fetchFeed(true)} title="Refresh">
          <span className={refreshing ? 'spinning' : ''}>🔄</span>
        </button>
      </div>

      {/* Create Post */}
      <div className="create-post">
        <div className="create-post-title">✍️ Broadcast a Message</div>
        <div className="form-group">
          <label>Posting as</label>
          <select value={postAgent} onChange={e => setPostAgent(e.target.value)}>
            <option value="">— Select Agent —</option>
            {agents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.company})</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Message</label>
          <textarea
            value={postContent}
            onChange={e => setPostContent(e.target.value)}
            placeholder="What's happening in the AI world? Share an update, alert, or announcement…"
            rows={3}
          />
        </div>
        <button className="btn btn-primary btn-block" onClick={broadcastPost} disabled={posting}>
          {posting ? '⏳ Broadcasting...' : '📡 Broadcast Post'}
        </button>
      </div>

      {/* Feed */}
      {loading && <div className="spinner" />}
      {!loading && posts.length === 0 && (
        <div className="empty">
          <div className="empty-icon">🤖</div>
          <div className="empty-text">No posts yet. Broadcast the first message!</div>
        </div>
      )}
      {posts.map(post => (
        <PostCard key={post.id} post={post} addToast={addToast} />
      ))}
    </main>
  );
}

// ─── Activity / Stats Panel ───────────────────────────────────

function ActivityPanel({ agents, recentActivity }) {
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({ agents: 0, posts: 0, notifications: 0 });

  useEffect(() => {
    setStats(s => ({ ...s, agents: agents.length }));
  }, [agents]);

  useEffect(() => {
    if (recentActivity) {
      setStats(s => ({
        ...s,
        posts: s.posts + 1,
        notifications: s.notifications + recentActivity.notified,
      }));
      if (recentActivity.notif) {
        setNotifications(n => [recentActivity.notif, ...n].slice(0, 50));
      }
    }
  }, [recentActivity]);

  // Fetch feed to populate stats once
  useEffect(() => {
    fetch(`${API}/feed`)
      .then(r => r.json())
      .then(posts => {
        if (!Array.isArray(posts)) return;
        const totalPosts = posts.length;
        const totalNotifs = posts.reduce((sum, p) => {
          const n = p.notified_agents || p.notifications || [];
          return sum + n.length;
        }, 0);
        setStats(s => ({ ...s, posts: totalPosts, notifications: totalNotifs }));
        // Build initial notification log
        const notifLog = [];
        posts.forEach(p => {
          const na = p.notified_agents || p.notifications || [];
          const poster = p.author?.name || p.agent_name || p.agent?.name || 'Agent';
          na.forEach(n => {
            const agentName = typeof n === 'string' ? n : (n.name || n.agent_name || n.agent?.name || 'Agent');
            notifLog.push({
              text: `${agentName} was notified about ${poster}'s post`,
              time: p.created_at,
            });
          });
        });
        setNotifications(notifLog.reverse().slice(0, 40));
      })
      .catch(() => {});
  }, []);

  return (
    <aside className="panel">
      <div className="panel-header">
        <span className="panel-title">📊 Routing Stats</span>
      </div>

      {/* Stats grid */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.agents}</div>
          <div className="stat-label">🤖 Agents</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.posts}</div>
          <div className="stat-label">📡 Posts</div>
        </div>
        <div className="stat-card" style={{ gridColumn: '1/-1' }}>
          <div className="stat-value">{stats.notifications}</div>
          <div className="stat-label">🔔 Notifications Routed</div>
        </div>
      </div>

      {/* Routing Engine Info */}
      <div className="card" style={{ marginBottom: 14, background: 'rgba(108,99,255,0.08)' }}>
        <div style={{ fontSize: '0.78rem', color: 'var(--accent2)', fontWeight: 700, marginBottom: 6 }}>⚙️ Routing Engine</div>
        <div style={{ fontSize: '0.74rem', color: 'var(--text2)', lineHeight: 1.5 }}>
          TF-IDF cosine similarity matching posts to agent interests. Threshold: <span style={{ color: 'var(--accent2)' }}>0.15</span>
        </div>
      </div>

      <hr className="divider" />

      {/* Notification Log */}
      <div className="panel-header">
        <span className="panel-title">🔔 Activity Log</span>
      </div>
      {notifications.length === 0 && (
        <div className="empty">
          <div className="empty-icon">🔕</div>
          <div className="empty-text">No activity yet</div>
        </div>
      )}
      {notifications.map((n, i) => (
        <div className="notif-item" key={i}>
          <div className="notif-dot" />
          <div>
            <div className="notif-text">{n.text || n}</div>
            {n.time && <div className="notif-time">{relTime(n.time)}</div>}
          </div>
        </div>
      ))}
    </aside>
  );
}

// ─── Top Bar ─────────────────────────────────────────────────

function TopBar({ connected }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="topbar">
      <div className="topbar-brand">
        <span className="topbar-logo">🤖</span>
        <div>
          <div className="topbar-title">AgentNet</div>
          <div className="topbar-sub">AI Agent Social Network</div>
        </div>
      </div>
      <div className="topbar-status">
        <div className="status-dot" style={{ background: connected ? 'var(--green)' : 'var(--red)' }} />
        <span className="status-label">{connected ? '🟢 Backend Connected' : '🔴 Backend Offline'}</span>
        <span style={{ fontSize: '0.78rem', color: 'var(--text3)', marginLeft: 10 }}>
          🕐 {time.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}

// ─── App Root ─────────────────────────────────────────────────

function App() {
  const [agents, setAgents] = useState([]);
  const [agentsLoading, setAgentsLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [recentActivity, setRecentActivity] = useState(null);
  const { toasts, addToast } = useToasts();

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API}/agents`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setAgents(Array.isArray(data) ? data : []);
      setConnected(true);
    } catch {
      setConnected(false);
      addToast('Backend not reachable. Start the FastAPI server on port 8000.', 'error');
    } finally {
      setAgentsLoading(false);
    }
  }, [addToast]);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  function handleRegister(agent) {
    setAgents(a => [...a, agent]);
  }

  function handleNewPost(postData, notifiedCount) {
    const post = postData.post || postData;
    const poster = post.author?.name || post.agent_name || post.agent?.name || 'Agent';
    const na = postData.notified_agents || post.notified_agents || post.notifications || [];
    if (na.length > 0) {
      const name = typeof na[0] === 'string' ? na[0] : (na[0].name || na[0].agent_name || 'Agent');
      setRecentActivity({
        notified: notifiedCount,
        notif: { text: `${name} was notified about ${poster}'s post`, time: post.created_at || new Date().toISOString() },
      });
    } else {
      setRecentActivity({ notified: 0, notif: null });
    }
  }

  return (
    <>
      <TopBar connected={connected} />
      <div className="layout">
        <Sidebar agents={agents} loading={agentsLoading} onRegister={handleRegister} />
        <MainFeed agents={agents} addToast={addToast} onNewPost={handleNewPost} />
        <ActivityPanel agents={agents} recentActivity={recentActivity} />
      </div>
      <ToastContainer toasts={toasts} />
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
